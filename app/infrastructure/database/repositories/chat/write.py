from datetime import datetime
from uuid import UUID
from app.infrastructure.database.models import Chat
from app.infrastructure.database.repositories.base import (
    BaseGetRepository,
    BaseSaveRepository,
    BaseUpdateRepository,
    BaseDeleteRepository,
)
from app.shared.dto.chat import ChatSaveDTO, ChatUpdateDTO
from app.shared.dto.enums import ChatType


class ChatRepository(
    BaseGetRepository[Chat],
    BaseSaveRepository[Chat, ChatSaveDTO],
    BaseUpdateRepository[Chat, ChatUpdateDTO],
    BaseDeleteRepository[Chat],
):
    """Репозиторий для записи чатов."""

    MODEL: type[Chat] = Chat

    async def set_active(self, chat_id: UUID, is_active: bool) -> Chat:
        """Поменять флаг активности."""
        chat = await self.get_record_by_id(chat_id)
        if chat.is_active != is_active:
            chat.is_active = is_active
            await self.session.flush()
        return chat

    async def update_type(self, chat_id: UUID, new_type: ChatType) -> Chat:
        """Поменять флаг активности."""
        chat = await self.get_record_by_id(chat_id)
        if chat.type != new_type:
            chat.type = new_type
            await self.session.flush()
        return chat

    async def touch_last_message(self, chat_id: UUID, at: datetime, message_id: UUID) -> Chat:
        """Обновить последнее сообщение."""
        chat = await self.get_record_by_id(chat_id)
        chat.last_message_at = at
        chat.last_message_id = message_id
        await self.session.flush()
        return chat