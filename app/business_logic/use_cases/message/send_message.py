from datetime import datetime, timezone
from uuid import uuid4
from app.business_logic.exceptions import PermissionError, TargetSendNotFound, ReplyMessageForwardedError
from app.business_logic.services import MessageService, ChatService
from app.business_logic.unit_of_work import UnitOfWork
from app.domain.events.audit import AuditEvent, Context
from app.domain.events.enums import ActionType
from app.infrastructure.redis import UnreadCache
from app.infrastructure.security import SymmetricEncode
from app.infrastructure.websocket import WSBroker
from app.shared.dto.audit import RequestMeta
from app.shared.dto.chat import ChatDTO, ChatSaveDTO, ChatMemberSaveDTO, ChatUpdateDTO
from app.shared.dto.enums import ChatType, ChatRole
from app.shared.dto.message import SendMessageCommand, MessageEncryptedSavedDTO
from app.shared.log_config import LogMixin


class SendMessageUseCase(LogMixin):
    """
    Отправить сообщение.

    Сценарий:
    - Получить или создать (приватный) чат.
    - Проверить, что отправитель является участником чата.
    - Сохранить сообщение.
    - Обновить последнее сообщение в БД.
    - Обновить счетчик непрочитанных сообщений.
    - Опубликовать в WSBroker (для всех воркеров).
    - Записать audit событие.
    """

    def __init__(
            self,
            message_service: MessageService,
            chat_service: ChatService,
            ws_broker: WSBroker,
            unread_cache: UnreadCache,
            uow: UnitOfWork,
            encoder: SymmetricEncode
    ):
        self._message_service = message_service
        self._chat_service = chat_service
        self._ws_broker = ws_broker
        self._unread_cache = unread_cache
        self._uow = uow
        self._encoder = encoder

    async def execute(
            self,
            msg: SendMessageCommand,
            actor_id: str,
            request_meta: RequestMeta
    ):
        if not msg.chat_id and not msg.recipient_id:
            raise TargetSendNotFound()

        if all([msg.reply_to_message_id, msg.forwarded_from_user_id, msg.forwarded_from_message_id]):
            raise ReplyMessageForwardedError()

        # Получить или создать (приватный) чат
        if msg.chat_id:
            chat = await self._chat_service.get(msg.chat_id)
        else:
            chat = await self._get_or_create_private_chat(actor_id, msg.recipient_id)

        # Проверить права
        is_member = await self._chat_service.get_member(chat.id, actor_id)
        if not is_member:
            self.log_warning(
                f"Пользователь {actor_id} не участник чата {chat.id}"
            )
            raise PermissionError(
                f"Пользователь {actor_id} не участник чата {chat.id}"
            )

        # Сохранить сообщение
        is_reply = bool(msg.reply_to_message_id)
        is_forwarded = bool(msg.forwarded_from_message_id)
        body_encrypted = self._encoder.encrypt(msg.text) if msg.text else None
        encrypt_msg_dto = MessageEncryptedSavedDTO(
            id=uuid4(),
            chat_id=chat.id,
            sender_id=actor_id,
            type=msg.type,
            reply_to_message_id=msg.reply_to_message_id,
            forwarded_from_message_id=msg.forwarded_from_message_id,
            forwarded_from_user_id=msg.forwarded_from_user_id,
            body_encrypted=body_encrypted,
            is_reply=is_reply,
            is_forwarded=is_forwarded
        )
        message = await self._message_service.save(encrypt_msg_dto)
        await self._chat_service.update(chat.id, ChatUpdateDTO(last_message_id=message.id))

        # Увеличить счетчик непрочитанных сообщений всем, кроме отправителя
        members = await self._chat_service.get_members(chat.id)
        for member in members:
            if member.user_id == actor_id:
                continue
            self._uow.add_after_commit(
                lambda uid=member.user_id: self._unread_cache.incr(
                    chat_id=chat.id,
                    user_id=uid,
                )
            )

        # Добавить сообщение в очередь для отправки после commit
        self._uow.add_after_commit(
            lambda: self._ws_broker.publish_to_chat(
                action_type="message",
                chat_id=chat.id,
                data={
                    "id": str(message.id),
                    "chat_id": str(message.chat_id),
                    "sender_id": message.sender_id,
                    "text": msg.text,
                    "created_at": message.created_at.isoformat(),
                },
            )
        )

        # Сохранить событие в audit
        self._uow.add_event(AuditEvent(
            actor_type=ActionType.SEND_MESSAGE,
            actor_id=actor_id,
            target_id=str(message.id),
            old_data=None,
            new_data={
                "chat_id": str(chat.id),
                "text_length": len(msg.text or ""),
                "type": msg.type.value,
            },
            context=Context(
                ip=request_meta.ip,
                user_agent=request_meta.user_agent,
                source=request_meta.source,
            ),
            occurred_at=datetime.now(tz=timezone.utc),
        ))

        self.log_info(f"Пользователь {actor_id} отправил сообщение {message.id}")
        return message

    async def _get_or_create_private_chat(self, user_1: str, user_2: str) -> ChatDTO:
        """Получить приватные чат или создать новый."""
        chat = await self._chat_service.find_between_users(user_1, user_2)
        if chat:
            return chat

        chat_id = uuid4()
        new_chat = await self._chat_service.save(ChatSaveDTO(
            id=chat_id,
            type=ChatType.PRIVATE,
        ))
        await self._chat_service.add_member(ChatMemberSaveDTO(
            chat_id=chat_id,
            user_id=user_1,
            role=ChatRole.MEMBER,
        ))
        await self._chat_service.add_member(ChatMemberSaveDTO(
            chat_id=chat_id,
            user_id=user_2,
            role=ChatRole.MEMBER,
        ))

        self.log_info(f"Создан личный чат {chat_id} между {user_1} и {user_2}")
        return new_chat
