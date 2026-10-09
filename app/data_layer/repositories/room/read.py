from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.data_layer.models import Room, ChatMember
from app.shared.dto.enums import ChatRole
from app.shared.dto.room import RoomDTO, RoomUserMemberDTO


class RoomReadRepository:
    """
    Репозиторий для чтения комнат (read-side).

    Возвращает DTO объекты и агрегированные данные для отдачи во внешние слои приложения.
    Не изменяет состояние БД.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, room_id: UUID) -> RoomDTO | None:
        """Получить комнату по ID или None."""
        stmt = (
            select(
                Room.chat_id,
                Room.title,
                Room.description,
                Room.avatar_url,
                Room.created_at,
                Room.updated_at
            )
            .where(Room.chat_id == room_id)
        )
        row = (await self.session.execute(stmt)).one_or_none()
        return RoomDTO(**row._mapping) if row else None

    async def get_user_rooms(self, user_id: str) -> list[RoomUserMemberDTO]:
        """Получить комнаты пользователя, его роль и кол-во участников."""
        members_count = (
            select(func.count(ChatMember.user_id))
            .where(ChatMember.chat_id == Room.chat_id)
            .correlate(Room)
            .scalar_subquery()
            .label("members_count")
        )

        stmt = (
            select(
                Room.chat_id,
                Room.title,
                Room.description,
                Room.avatar_url,
                ChatMember.user_id,
                ChatMember.role,
                members_count,
                Room.created_at,
                Room.updated_at
            )
            .join(ChatMember, ChatMember.chat_id == Room.chat_id)
            .where(ChatMember.user_id == user_id)
            .order_by(Room.title)
        )
        rows = (await self.session.execute(stmt)).all()
        return [
            RoomUserMemberDTO(**row._mapping)
            for row in rows
        ]

    async def get_owner_room(self, room_id: UUID) -> str | None:
        """
        Получить идентификатор владельца комнаты или None.

        Возвращает None, если владелец не найден.

        :param room_id: Идентификатор комнаты.
        :return: ID владельца или None, если владелец не задан.
        """
        stmt = (
            select(ChatMember.user_id)
            .where(
                ChatMember.role == ChatRole.OWNER,
                ChatMember.chat_id == room_id
            )
            .limit(1)
        )
        return await self.session.scalar(stmt)

    async def is_member(self, room_id: UUID, user_id: str) -> bool:
        """Является ли пользователь участником комнаты."""
        stmt = (
            select(ChatMember.user_id)
            .where(
                ChatMember.chat_id == room_id,
                ChatMember.user_id == user_id,
            )
            .limit(1)
        )
        return await self.session.scalar(stmt) is not None