from uuid import UUID
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

from app.data_layer.exceptions import RecordNotFound
from app.data_layer.repositories.base import BaseRepository
from app.shared.dto.room import RoomDtoUpdate, RoomMemberDtoSave, RoomDtoSave
from app.data_layer.models import Room, RoomRole, RoomMember


class RoomRepository(BaseRepository[Room]):
    """Репозиторий для работы с данными комнат"""
    MODEL: type[Room] = Room
    ROOM_MEMBER_MODEL: type[RoomMember] = RoomMember

    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self.MAPPING_DTO_ORM_SAVE.update({
            RoomDtoSave: Room,
            RoomMemberDtoSave: RoomMember
        })

    async def get_rooms(self, limit: int, offset: int, with_relation: bool = False) -> list[Room]:
        """Получение списка комнат"""
        options = None
        if with_relation:
            options = self._with_room_options()
        result = await self._get(limit, offset, options)
        return result

    async def get_member_in_room(self, room_id: UUID, with_relation: bool = False) -> list[RoomMember]:
        """Получение участников комнаты"""
        stmt = select(self.ROOM_MEMBER_MODEL).where(self.ROOM_MEMBER_MODEL.room_id == room_id)
        if with_relation:
            stmt = stmt.options(*self._with_room_member_options())
        sqla_obj = await self.session.execute(stmt)
        return list(sqla_obj.scalars().all())

    async def get_room_by_id(self, room_id: UUID, with_relation: bool = False) -> Room:
        """Получение комнаты по id"""
        options = None
        if with_relation:
            options = self._with_room_options()
        result = await self._get_by_id(room_id, options)
        return result

    async def add_member_in_room(self, room_member: RoomMemberDtoSave) -> RoomMember:
        """Добавление участника в комнату"""
        raw_data = room_member.model_dump()
        orm_model = self.ROOM_MEMBER_MODEL(**raw_data)
        self.session.add(orm_model)
        await self.session.flush()
        return orm_model

    async def update_room(self, room_id: UUID, update_room: RoomDtoUpdate) -> Room:
        """Обновление информации о комнате"""
        result = await self.update(room_id, update_room)
        return result

    async def update_role_member_in_room(self, room_id: UUID, user_id: str, new_role: RoomRole) -> RoomMember:
        """Обновить роль участника комнаты"""
        stmt = (
            select(self.ROOM_MEMBER_MODEL)
            .where(
                and_(
                    self.ROOM_MEMBER_MODEL.room_id == room_id,
                    self.ROOM_MEMBER_MODEL.user_id == user_id)
            )
        )
        sqla_obj = await self.session.execute(stmt)
        member = sqla_obj.scalar_one_or_none()
        if not member:
            raise RecordNotFound(f'room={room_id}, user={user_id}', self.MODEL, 'id')
        member.role = new_role
        return member

    def _with_room_options(self):
        """Получение relation для жадной загрузки"""
        return [
            joinedload(self.MODEL.owner),
            selectinload(self.MODEL.members),
            joinedload(self.MODEL.chat)
        ]

    def _with_room_member_options(self):
        """Получение relation для жадной загрузки"""
        return [
            joinedload(self.ROOM_MEMBER_MODEL.room),
            joinedload(self.ROOM_MEMBER_MODEL.user),
        ]