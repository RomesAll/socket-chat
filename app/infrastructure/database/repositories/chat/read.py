from typing import Any, Sequence
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.database.models import Chat, ChatMember, User, Message, Room
from app.shared.dto.chat import ChatDTO, PrivateChatDTO, GroupChatDTO
from app.shared.dto.enums import ChatType
from sqlalchemy import select, func
from sqlalchemy.orm import aliased

from app.shared.dto.message import MessageBriefGetDTO, MessageBriefEncryptedGetDTO


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
            .select_from(ChatMember)
            .join(Chat, Chat.id == ChatMember.chat_id)
            .where(
                ChatMember.user_id.in_([user_2, user_1]),
                Chat.type == ChatType.PRIVATE
            )
            .group_by(
                Chat.id,
                Chat.type,
                Chat.is_active,
                Chat.last_message_id,
                Chat.last_message_at,
                Chat.created_at,
                Chat.updated_at
            )
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

    async def get_user_chat_ids(self, user_id: str) -> list[UUID]:
        """Чаты пользователя, отсортированные по последнему сообщению."""
        stmt = (
            select(
                Chat.id,
            )
            .join(ChatMember, ChatMember.chat_id == Chat.id)
            .where(ChatMember.user_id == user_id)
            .order_by(Chat.last_message_at.desc().nullslast())
        )
        rows = (await self.session.execute(stmt)).scalars().all()
        return rows

    async def get_private_chats_preview(self, user_id: str) -> Sequence[Any]:
        """Получить preview приватных чатов (включая Избранное)"""
        user_chats = (
            select(ChatMember.chat_id)
            .where(ChatMember.user_id == user_id)
        )

        private_chats = (
            select(ChatMember.chat_id)
            .group_by(ChatMember.chat_id)
            .having(func.count(ChatMember.user_id) <= 2)
        )

        companion = aliased(ChatMember)

        stmt = (
            select(
                Chat.id,
                Chat.type,
                Chat.last_message_id,
                User.avatar_url.label('other_user_avatar'),
                User.id.label("other_user_id"),
                User.display_name.label("other_user_name"),
                Message.body_encrypted.label("last_message_body"),
                Message.type.label("last_message_type"),
                Message.sender_id.label("last_message_sender_id"),
                Message.created_at.label("last_message_created_at")
            )
            .where(
                Chat.id.in_(user_chats),
                Chat.id.in_(private_chats),
                Chat.type.in_([ChatType.PRIVATE, ChatType.FAVORITES]),  # <-- ИЗМЕНЕНО
            )
            .outerjoin(
                companion,
                (companion.chat_id == Chat.id) & (companion.user_id != user_id)
            )
            .outerjoin(User, User.id == companion.user_id)
            .outerjoin(Message, Message.id == Chat.last_message_id)
        )

        rows = (await self.session.execute(stmt)).all()
        return rows

    async def get_group_chats_preview(self, user_id: str) -> Sequence[Any]:
        """Получить preview групповых чатов"""
        user_chats = (
            select(ChatMember.chat_id)
            .where(ChatMember.user_id == user_id)
        )

        stmt = (
            select(
                Chat.id,
                Chat.last_message_id,
                Room.title.label("room_title"),
                Room.avatar_url.label("room_avatar"),
                ChatMember.role.label("my_role"),
                Message.body_encrypted.label("last_message_body"),
                Message.type.label("last_message_type"),
                Message.sender_id.label("last_message_sender_id"),
                Message.created_at.label("last_message_created_at")
            )
            .where(
                Chat.id.in_(user_chats),
                Chat.type == ChatType.ROOM,
                Chat.is_active == True,
            )
            .join(Room, Room.chat_id == Chat.id)
            .join(ChatMember, (ChatMember.chat_id == Chat.id) & (ChatMember.user_id == user_id))
            .outerjoin(Message, Message.id == Chat.last_message_id)
            .order_by(Chat.last_message_at.desc().nullslast())
        )

        rows = (await self.session.execute(stmt)).all()
        return rows

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