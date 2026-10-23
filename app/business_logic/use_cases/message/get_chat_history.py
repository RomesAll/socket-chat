from uuid import UUID
from app.business_logic.exceptions import PermissionError
from app.business_logic.services import ChatService, MessageService
from app.infrastructure.security import SymmetricEncode
from app.shared.dto.message import MessageGetDTO, MessageEncryptedGetDTO, ReplyMessageDTO, \
    ForwardedMessageDTO


class GetChatHistoryUseCase:
    """
    Получить историю сообщений чата.

    Сценарий:
    - Проверить, что актор — участник.
    - Получить зашифрованные сообщения.
    - Расшифровать текст.
    """

    def __init__(
        self,
        chat_service: ChatService,
        message_service: MessageService,
        cipher: SymmetricEncode,
    ):
        self._chat_service = chat_service
        self._message_service = message_service
        self._cipher = cipher

    async def execute(
        self,
        chat_id: UUID,
        limit: int,
        before_id: UUID | None,
        actor_id: str,
    ) -> list[MessageGetDTO]:
        # Проверить права
        is_member = await self._chat_service.is_member(chat_id, actor_id)
        if not is_member:
            raise PermissionError(
                f"Пользователь {actor_id} не участник чата {chat_id}"
            )

        # Получить зашифрованные сообщения
        encrypted_messages = await self._message_service.get_message_by_chat(
            chat_id=chat_id,
            limit=limit,
            before_id=before_id
        )

        return [self._decrypt(msg) for msg in encrypted_messages]

    def _decrypt(self, msg: MessageEncryptedGetDTO) -> MessageGetDTO:
        """Расшифровать тело сообщения."""
        reply_to, forwarded_from = None, None

        text_message = (
            self._cipher.decrypt(msg.body_encrypted)
            if msg.body_encrypted
            else None
        )

        if msg.reply_to:
            text_reply_message = (
                self._cipher.decrypt(msg.reply_to.body_encrypted)
                if msg.reply_to.body_encrypted
                else None
            )
            reply_to = ReplyMessageDTO(
                id=msg.reply_to.id,
                type=msg.reply_to.type,
                text=text_reply_message
            )

        if msg.forwarded_from:
            text_forwarded_message = (
                self._cipher.decrypt(msg.forwarded_from.body_encrypted)
                if msg.forwarded_from and msg.forwarded_from.body_encrypted
                else None
            )
            forwarded_from = ForwardedMessageDTO(
                forwarded_from_message_id=msg.forwarded_from.forwarded_from_message_id,
                forwarded_from_user_id=msg.forwarded_from.forwarded_from_user_id,
                type=msg.forwarded_from.type,
                text=text_forwarded_message
            )

        return MessageGetDTO(
            id=msg.id,
            chat_id=msg.chat_id,
            sender_id=msg.sender_id,
            type=msg.type,
            reply_to=reply_to,
            forwarded_from=forwarded_from,
            text=text_message,
            is_edited=msg.is_edited,
            created_at=msg.created_at,
            updated_at=msg.updated_at,
            files=msg.files
        )