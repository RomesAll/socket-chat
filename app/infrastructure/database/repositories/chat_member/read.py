from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.database.models import ChatMember
from app.shared.dto.chat import ChatMemberDTO
from app.shared.dto.enums import ChatRole


class ChatMemberReadRepository:
    """Репозиторий для чтения участников чата."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_ids(self, chat_id: UUID, user_id: str) -> ChatMemberDTO | None:
        """Участник по составному ключу или None."""
        stmt = (
            select(
                ChatMember.chat_id,
                ChatMember.user_id,
                ChatMember.role,
                ChatMember.mute,
                ChatMember.last_read_message_id,
                ChatMember.created_at,
                ChatMember.updated_at
            )
            .where(
                ChatMember.chat_id == chat_id,
                ChatMember.user_id == user_id,
            )
        )
        row = (await self.session.execute(stmt)).one_or_none()
        return ChatMemberDTO(**row._mapping) if row else None

    async def list_by_chat(self, chat_id: UUID) -> list[ChatMemberDTO]:
        """Участники чата."""
        stmt = (
            select(
                ChatMember.chat_id,
                ChatMember.user_id,
                ChatMember.role,
                ChatMember.mute,
                ChatMember.last_read_message_id,
                ChatMember.created_at,
                ChatMember.updated_at
            )
            .where(ChatMember.chat_id == chat_id)
            .order_by(ChatMember.role, ChatMember.user_id)
        )
        rows = (await self.session.execute(stmt)).all()
        return [ChatMemberDTO(**row._mapping) for row in rows]

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

    async def is_admin(self, chat_id: UUID, user_id: str) -> bool:
        """Является ли пользователь owner или admin."""
        stmt = (
            select(ChatMember.user_id)
            .where(
                ChatMember.chat_id == chat_id,
                ChatMember.user_id == user_id,
                ChatMember.role.in_([ChatRole.OWNER, ChatRole.ADMIN]),
            )
            .limit(1)
        )
        return await self.session.scalar(stmt) is not None

    async def is_owner(self, chat_id: UUID, user_id: str) -> bool:
        """Является ли пользователь owner или admin."""
        stmt = (
            select(ChatMember.user_id)
            .where(
                ChatMember.chat_id == chat_id,
                ChatMember.user_id == user_id,
                ChatMember.role.in_([ChatRole.OWNER,]),
            )
            .limit(1)
        )
        return await self.session.scalar(stmt) is not None