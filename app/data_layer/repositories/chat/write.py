from datetime import datetime
from uuid import UUID
from app.data_layer.models import Chat
from app.data_layer.repositories.base import (
    BaseGetRepository,
    BaseSaveRepository,
    BaseUpdateRepository,
    BaseDeleteRepository,
)
from app.shared.dto.chat import ChatSaveDTO, ChatUpdateDTO


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
        chat.is_active = is_active
        await self.session.flush()
        return chat

    async def touch_last_message_at(self, chat_id: UUID, at: datetime) -> Chat:
        """Обновить время последнего сообщения."""
        chat = await self.get_record_by_id(chat_id)
        chat.last_message_at = at
        await self.session.flush()
        return chat