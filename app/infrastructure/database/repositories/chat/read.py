from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.database.models import Chat, ChatMember
from app.shared.dto.chat import ChatDTO
from app.shared.dto.enums import ChatType


class ChatReadRepository:
    """Репозиторий для чтения чатов."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def find_between_users(self, user_1: str, user_2: str) -> ChatDTO | None:
        """Получить чат между двумя пользователями"""
        stmt = (
            select(
                Chat.id,
                Chat.type,
                Chat.is_active,
                Chat.last_message_id,
                Chat.last_message_at,
                Chat.created_at,
                Chat.updated_at
            )
            .join(Chat, Chat.id == ChatMember.chat_id)
            .where(
                ChatMember.user_id.in_([user_2, user_1]),
                Chat.type == ChatType.PRIVATE
            )
            .group_by(ChatMember.chat_id)
            .having(func.count(func.distinct(ChatMember.user_id)) == 2)
        )
        row = (await self.session.execute(stmt)).one_or_none()
        return ChatDTO(**row._mapping) if row else None

    async def find_chosen_id(self, user_id: str) -> UUID | None:
        """Получить мой чат с самим собой"""
        single_chat_sub = (
            select(ChatMember.chat_id, ChatMember.user_id)
            .group_by(ChatMember.chat_id)
            .having(func.count(ChatMember.user_id) == 1)
            .subquery()
        )

        stmt = (
            select(single_chat_sub.c.chat_id)
            .join(Chat, Chat.id == single_chat_sub.c.chat_id)
            .where(
                single_chat_sub.c.user_id == user_id,
                Chat.type == ChatType.PRIVATE
            )
        )
        result = (await self.session.execute(stmt)).one_or_none()
        return result

    async def find_by_id(self, chat_id: UUID) -> ChatDTO | None:
        """Чат по id или None."""
        stmt = (
            select(
                Chat.id,
                Chat.type,
                Chat.is_active,
                Chat.last_message_id,
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