from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.data_layer.models import Chat, ChatMember
from app.shared.dto.chat import ChatDTO


class ChatReadRepository:
    """Репозиторий для чтения чатов."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, chat_id: UUID) -> ChatDTO | None:
        """Чат по id или None."""
        stmt = (
            select(
                Chat.id,
                Chat.type,
                Chat.is_active,
                Chat.last_message_at,
                Chat.created_at,
                Chat.updated_at
            )
            .where(Chat.id == chat_id)
        )
        row = (await self.session.execute(stmt)).one_or_none()
        return ChatDTO(**row._mapping) if row else None

    async def get_user_chats(self, user_id: str) -> list[ChatDTO]:
        """Чаты пользователя, отсортированные по последнему сообщению."""
        stmt = (
            select(
                Chat.id,
                Chat.type,
                Chat.is_active,
                Chat.last_message_at,
                Chat.created_at,
                Chat.updated_at
            )
            .join(ChatMember, ChatMember.chat_id == Chat.id)
            .where(ChatMember.user_id == user_id)
            .order_by(Chat.last_message_at.desc().nullslast())
        )
        rows = (await self.session.execute(stmt)).all()
        return [ChatDTO(**row._mapping) for row in rows]

    async def is_member(self, chat_id: UUID, user_id: str) -> bool:
        """Является ли пользователь участником чата."""
        stmt = (
            select(ChatMember.user_id)
            .where(
                ChatMember.chat_id == chat_id,
                ChatMember.user_id == user_id,
            )
            .limit(1)
        )
        return await self.session.scalar(stmt) is not None