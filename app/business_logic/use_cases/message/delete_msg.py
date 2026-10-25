from datetime import datetime, timezone
from uuid import UUID
from app.business_logic.exceptions import PermissionError
from app.business_logic.services import ChatService, MessageService
from app.business_logic.unit_of_work import UnitOfWork
from app.domain.events.audit import AuditEvent, Context
from app.domain.events.enums import ActionType
from app.infrastructure.database.exceptions import RecordNotFound
from app.infrastructure.websocket import WSBroker
from app.shared.dto.audit import RequestMeta
from app.shared.dto.base import UNSET
from app.shared.dto.chat import ChatUpdateDTO
from app.shared.dto.enums import ChatRole
from app.shared.log_config import LogMixin


class DeleteMessageUseCase(LogMixin):
    """
    Удалить сообщение.

    Сценарий:
    - Проверить права (автор или админ).
    - Удалить сообщение.
    - Если это было последнее сообщение — обновить превью чата.
    - Опубликовать в WebSocket.
    - Записать audit-событие.
    - Очистить кеш истории.
    """

    def __init__(
            self,
            message_service: MessageService,
            chat_service: ChatService,
            ws_broker: WSBroker,
            uow: UnitOfWork,
    ):
        self._message_service = message_service
        self._chat_service = chat_service
        self._ws_broker = ws_broker
        self._uow = uow

    async def execute(
            self,
            message_id: UUID,
            actor_id: str,
            request_meta: RequestMeta,
    ):
        time_now = datetime.now(tz=timezone.utc)

        # Получить сообщение
        message = await self._message_service.get(message_id)
        actor = await self._chat_service.get_member(message.chat_id, actor_id)
        message_owner = None

        try:
            if message.sender_id:
                message_owner = await self._chat_service.get_member(message.chat_id, message.sender_id)
        except RecordNotFound:
            pass

        can_manage = False
        if message_owner:
            can_manage = actor.role.can_manage(message_owner.role)
        else:
            can_manage = actor.role in [ChatRole.ADMIN, ChatRole.OWNER]

        if actor_id != message.sender_id and not can_manage:
            self.log_warning(
                f"Пользователь {actor_id} пытался удалить сообщение {message_id}"
            )
            raise PermissionError(
                f"Пользователь {actor_id} не может удалить сообщение {message_id}"
            )

        # Удалить сообщение
        await self._message_service.delete(message_id)

        # Обновить превью чата, если удалили последнее сообщение
        chat = await self._chat_service.get(message.chat_id)
        if chat.last_message_id == message_id:
            prev_message = await self._message_service.get_previous_message(
                chat_id=message.chat_id,
                before_date=message.created_at
            )

            await self._chat_service.update(chat.id, ChatUpdateDTO(
                last_message_id=prev_message.id if prev_message else UNSET,
                last_message_at=prev_message.created_at if prev_message else UNSET
            ))

        # Отправить событие удаления по WebSocket
        self._uow.add_after_commit(
            lambda: self._ws_broker.publish_to_chat(
                action_type="message_deleted",
                chat_id=message.chat_id,
                data={"id": str(message_id)},
            )
        )

        # Сохранить событие в Audit
        self._uow.add_event(AuditEvent(
            actor_type=ActionType.DELETE_MESSAGE_IN_CHAT,
            actor_id=actor_id,
            target_id=str(message_id),
            old_data={
                "chat_id": str(message.chat_id),
                "sender_id": message.sender_id,
                "type": message.type.value,
            },
            new_data=None,
            context=Context(
                ip=request_meta.ip,
                user_agent=request_meta.user_agent,
                source=request_meta.source,
            ),
            occurred_at=time_now,
        ))

        self.log_info(
            f"Пользователь {actor_id} удалил сообщение {message_id}"
        )