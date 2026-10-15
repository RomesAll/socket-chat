from uuid import UUID
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.database.models import Room, ChatMember
from app.shared.dto.enums import ChatRole
from app.shared.dto.room import RoomDTO, RoomUserMemberDTO, TopRoomsByMemberDTO


class RoomReadRepository:
    """
    Репозиторий для чтения комнат (read-side).

    Возвращает DTO объекты и агрегированные данные для отдачи во внешние слои приложения.
    Не изменяет состояние БД.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def top_rooms_by_member(self, top_count: int) -> list[TopRoomsByMemberDTO]:
        """
        Поучить список комнат по наибольшему кол-ву участников
        :param top_count: Кол-во комнат для получения.
        :return:
        """
        members_count = func.count(ChatMember.user_id).label("members_count")

        owner_subquery = (
            select(ChatMember.user_id)
            .where(
                ChatMember.chat_id == Room.chat_id,
                ChatMember.role == ChatRole.OWNER,
            )
            .scalar_subquery()
            .label("owner_id")
        )

        stmt = (
            select(
                Room.chat_id,
                Room.max_users,
                members_count,
                owner_subquery,
                Room.created_at,
            )
            .join(ChatMember, ChatMember.chat_id == Room.chat_id)
            .group_by(Room.chat_id, Room.created_at, Room.max_users)
            .order_by(desc(members_count))
            .limit(top_count)
        )
        rows = (await self.session.execute(stmt)).all()
        return [TopRoomsByMemberDTO(**row._mapping) for row in rows]

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

    async def get_owner_rooms_with_members(
            self, owner_id: str,
    ) -> tuple[list[UUID], dict[UUID, list[tuple[str, ChatRole]]]]:
        """
        Возвращает:
        - список id комнат владельца;
        - dict[chat_id, list[(user_id, role)]] — все участники этих комнат.
        """
        # 1) id комнат владельца
        owner_rooms_stmt = (
            select(Room.chat_id)
            .join(ChatMember, ChatMember.chat_id == Room.chat_id)
            .where(
                ChatMember.user_id == owner_id,
                ChatMember.role == ChatRole.OWNER,
            )
        )
        room_ids = list((await self.session.scalars(owner_rooms_stmt)).all())
        if not room_ids:
            return [], {}

        # 2) все участники этих комнат
        members_stmt = (
            select(ChatMember.chat_id, ChatMember.user_id, ChatMember.role)
            .where(ChatMember.chat_id.in_(room_ids))
        )
        rows = (await self.session.execute(members_stmt)).all()

        members_by_room: dict[UUID, list[tuple[str, ChatRole]]] = {}
        for chat_id, user_id, role in rows:
            members_by_room.setdefault(chat_id, []).append((user_id, role))

        return room_ids, members_by_room

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