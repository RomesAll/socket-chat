from uuid import UUID
from sqlalchemy import select, func
from app.data_layer.repositories.base.base_repo import BaseRepository
from app.data_layer.models import Room, RoomMember
from app.shared.dto.room import RoomDTO, RoomListItemDTO


class RoomReadRepository(BaseRepository):
    """
    Репозиторий для чтения комнат (read-side).

    Возвращает DTO объекты и агрегированные данные для отдачи во внешние слои приложения.
    Не изменяет состояние БД.
    """

    MODEL: type[Room] = Room

    async def get_by_id(self, room_id: UUID) -> RoomDTO | None:
        """Получить комнату по ID или None."""
        stmt = (
            select(
                Room.id,
                Room.name,
                Room.description,
                Room.avatar_url,
                Room.owner_id,
            )
            .where(Room.id == room_id)
        )
        row = (await self.session.execute(stmt)).one_or_none()
        return RoomDTO(**row._mapping) if row else None

    async def get_user_rooms(self, user_id: str) -> list[RoomListItemDTO]:
        """Получить комнаты пользователя, его роль и кол-во участников."""
        stmt = (
            select(
                Room.id,
                Room.name,
                Room.avatar_url,
                Room.owner_id,
                RoomMember.role,
            )
            .join(RoomMember, RoomMember.room_id == Room.id)
            .where(RoomMember.user_id == user_id)
            .order_by(Room.name)
        )
        rows = (await self.session.execute(stmt)).all()
        room_ids = [row.id for row in rows]

        counts: dict[UUID, int] = {}
        if room_ids:
            count_stmt = (
                select(RoomMember.room_id, func.count(RoomMember.user_id))
                .where(RoomMember.room_id.in_(room_ids))
                .group_by(RoomMember.room_id)
            )
            count_rows = (await self.session.execute(count_stmt)).all()
            counts = {room_id: cnt for room_id, cnt in count_rows}

        return [
            RoomListItemDTO(
                id=row.id,
                name=row.name,
                avatar_url=row.avatar_url,
                owner_id=row.owner_id,
                role=row.role,
                members_count=counts.get(row.id, 0),
            )
            for row in rows
        ]

    async def is_member(self, room_id: UUID, user_id: str) -> bool:
        """Является ли пользователь участником комнаты."""
        stmt = (
            select(RoomMember.user_id)
            .where(
                RoomMember.room_id == room_id,
                RoomMember.user_id == user_id,
            )
            .limit(1)
        )
        return await self.session.scalar(stmt) is not None