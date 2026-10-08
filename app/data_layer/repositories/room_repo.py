from typing import Sequence
from uuid import UUID
from sqlalchemy import select, and_

from app.business_logic.exceptions import OwnerInRoomEmpty
from app.data_layer.exceptions import RecordNotFound
from app.data_layer.repositories.base_repo import (
    BaseGetRepository,
    BaseSaveRepository,
    BaseUpdateRepository,
    BaseDeleteRepository
)
from app.shared.dto.room import RoomDtoUpdate, RoomDtoSave
from app.data_layer.models import Room, RoomRole, RoomMember


class RoomRepository(
    BaseGetRepository[Room],
    BaseSaveRepository[Room, RoomDtoSave],
    BaseUpdateRepository[Room, RoomDtoUpdate],
    BaseDeleteRepository[Room]
):
    """Репозиторий для работы с комнатами"""

    MODEL: type[Room] = Room
    ROOM_MEMBER_MODEL: type[RoomMember] = RoomMember

    async def get_user_rooms(self, user_id: str) -> Sequence[Room]:
        """
        Получение информации о комнатах, в которых состоит пользователь
        :param user_id: идентификатор пользователя
        :return: Sequence объекты orm модели Room
        """
        stmt = (
            select(self.MODEL)
            .join(self.ROOM_MEMBER_MODEL, self.ROOM_MEMBER_MODEL.room_id == self.MODEL.id)
            .where(self.ROOM_MEMBER_MODEL.user_id == user_id)
        )
        results = await self.session.scalars(stmt)
        return results.all()

    async def get_room_member(self, room_id: UUID, member_id: str) -> RoomMember:
        """
        Получение участника комнаты
        :param room_id: id комнаты
        :param member_id: id участника
        :return:
        """
        stmt = (
            select(self.ROOM_MEMBER_MODEL)
            .where(self.ROOM_MEMBER_MODEL.room_id == room_id)
        )
        result = await self.session.scalar(stmt)
        if not result:
            raise RecordNotFound(
                [member_id, room_id],
                self.ROOM_MEMBER_MODEL.__tablename__,
                'user_id, room_id'
            )
        return result

    async def get_room_members(self, room_id: UUID) -> Sequence[RoomMember]:
        """
        Получение информации об участниках комнаты
        :param room_id: идентификатор комнаты
        :return: Sequence объекты orm модели RoomMember
        """
        stmt = (
            select(self.ROOM_MEMBER_MODEL)
            .where(self.ROOM_MEMBER_MODEL.room_id == room_id)
        )
        results = await self.session.scalars(stmt)
        return results.all()

    async def add_room_member_def_user(self, room_id: UUID, user_id: str) -> RoomMember:
        """
        Добавление нового участника в комнату
        :param user_id: id пользователя
        :param room_id: id комнаты
        :return: новый объект orm модели RoomMember
        """
        orm_model = self.ROOM_MEMBER_MODEL(
            room_id=room_id,
            user_id=user_id
        )
        self.session.add(orm_model)
        await self.session.flush()
        return orm_model

    async def add_room_member_owner(self, room_id: UUID, user_id: str) -> RoomMember:
        """
        Добавление владельца в комнату
        :param user_id: id пользователя
        :param room_id: id комнаты
        :return: новый объект orm модели RoomMember
        """
        orm_model = self.ROOM_MEMBER_MODEL(
            room_id=room_id,
            user_id=user_id,
            role=RoomRole.OWNER,
            is_access_private_chat=True
        )
        self.session.add(orm_model)
        await self.session.flush()
        return orm_model

    async def remove_room_member(self, room_id: UUID, user_id: str) -> RoomMember:
        """
        Удалить участника из комнаты
        :param room_id: id комнаты
        :param user_id: id пользователя
        :return: удаленный объекты orm модели ChatMember
        """
        stmt_exist = (
            select(self.ROOM_MEMBER_MODEL)
            .where(
                self.ROOM_MEMBER_MODEL.user_id == user_id,
                self.ROOM_MEMBER_MODEL.room_id == room_id
            )
        )
        room_member = await self.session.scalar(stmt_exist)
        if not room_member:
            raise RecordNotFound(
                [user_id, room_id],
                self.ROOM_MEMBER_MODEL.__tablename__,
                'user_id, room_id'
            )
        await self.session.delete(room_member)
        await self.session.flush()
        return room_member

    async def update_role_member_in_room(self, room_id: UUID, user_id: str, new_role: RoomRole) -> RoomMember:
        """
        Обновить роль участника комнаты
        :param room_id: идентификатор комнаты
        :param user_id: идентификатор пользователя
        :param new_role: новая роль
        :return: обновленный объекты orm модели RoomMember
        """
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
            raise RecordNotFound(f'room={room_id}, user={user_id}', self.MODEL.__tablename__, 'id')
        member.role = new_role
        await self.session.flush()
        return member

    async def change_owner(self, room_id: UUID, new_owner: str) -> Room:
        """
        Сменить владельца комнаты
        :param room_id: id комнаты
        :param new_owner: новый владелец комнаты
        :return:
        """
        room_info = await self.get_record_by_id(room_id)
        member = await self.get_room_member(room_id, new_owner)
        room_info.owner_id = member.user_id
        member.is_access_private_chat = True
        member.role = RoomRole.OWNER
        await self.session.flush()
        return room_info

    async def get_room_owner(self, room_id: UUID) -> str:
        """
        Получение владельца комнаты
        :param room_id: id комнаты
        :return:
        """
        stmt = (
            select(self.MODEL.owner_id)
            .where(self.MODEL.id == room_id)
        )
        result = await self.session.scalar(stmt)
        if not result:
            raise OwnerInRoomEmpty(room_id)
        return result

    async def get_user_owner_rooms(self, user_id: str) -> Sequence[Room]:
        """
        Получить комнаты, в которых пользователь является владельцем
        :param user_id: id пользователя
        :return:
        """
        stmt = (
            select(self.MODEL)
            .where(self.MODEL.owner_id == user_id)
        )
        results = await self.session.scalars(stmt)
        return results.all()