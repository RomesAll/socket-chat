from uuid import UUID
from app.business_logic.redis_adapter import Cache
from app.data_layer.models.events import EventType
from app.business_logic.unit_of_work import UnitOfWork
from app.shared.dto.chat import ChatDtoGet
from app.shared.dto.dto_relation_ship import RoomDtoGetWithRelation
from app.shared.dto.room import (
    RoomDtoSave,
    RoomMemberDtoSave,
    RoomDtoGet,
    RoomMemberDtoGet
)
from app.shared.dto.user import UserDtoBriefGet
from app.shared.log_config import LogMixin
from app.shared.config import get_config, AppMode, BaseConfig


def _get_config() -> BaseConfig:
    return get_config()


class RoomService(LogMixin):
    """Сервис для управления комнатами"""
    def __init__(self, uow: UnitOfWork, cache: Cache):
        self._uow = uow
        self._cache = cache

    async def add_room(self, new_room: RoomDtoSave) -> RoomDtoGet:
        """Добавление новой комнаты"""
        async with self._uow as uow:
            room_orm = await uow.room_repo.save(new_room)
            self.log_info(f'Пользователь {new_room.owner_id} успешно создал комнату с id {new_room.id}')
            chats_dto = [ChatDtoGet(**chat.to_dict()) for chat in room_orm.chats]
            members_dto = [RoomMemberDtoGet(**member.to_dict()) for member in room_orm.members]
            owner_dto = UserDtoBriefGet(**room_orm.owner.to_dict())
            response = RoomDtoGetWithRelation(
                **room_orm.to_dict(), chats=chats_dto, members=members_dto, owner=owner_dto
            )
            if _get_config().mode not in (AppMode.DEV,):
                uow.add_event(
                    event_name='Save new room',
                    payload=response.model_dump(),
                    event_type=EventType.CRETE_NEW_ROOM
                )
                self.log_info(f'Событие {EventType.CRETE_NEW_ROOM} зарегистрировано')
        is_saved = await self._cache.save_room(
            RoomDtoGet.model_dump(response)
        )
        if not is_saved:
            self.log_warning(f'Комната {new_room.id} не была сохранена в кеше')
        return response

    async def get_rooms(self, limit: int, offset: int) -> list[RoomDtoGet]:
        """Получение комнат"""
        async with self._uow as uow:
            list_room_orm = await uow.room_repo.get_rooms(limit, offset, with_relation=False)
            response = [
                RoomDtoGet(**room_orm.to_dict())
                for room_orm in list_room_orm
            ]
            return response

    async def get_rooms_with_relation(self, limit: int, offset: int) -> list[RoomDtoGetWithRelation]:
        """Получение комнат с relationship"""
        async with self._uow as uow:
            list_room_orm = await uow.room_repo.get_rooms(limit, offset, with_relation=True)
            response = [
                RoomDtoGetWithRelation(
                    **room_orm.to_dict(),
                    owner=room_orm.owner,
                    members=[RoomMemberDtoGet(**member.to_dict()) for member in room_orm.members],
                    chats=[ChatDtoGet(**chat.to_dict()) for chat in room_orm.chats]
                )
                for room_orm in list_room_orm
            ]
            return response

    async def get_room_by_id(self, room_id: UUID) -> RoomDtoGet:
        """Получить комнату по id с relationship"""
        cache_data = await self._cache.get_room_info(room_id)
        if cache_data:
            return RoomDtoGet(**cache_data)

        async with self._uow as uow:
            room_orm = await uow.room_repo.get_room_by_id(room_id)
            response = RoomDtoGet(**room_orm.to_dict())

        is_saved = await self._cache.save_room(response)
        if not is_saved:
            self.log_warning(f'Комната {room_id} не была сохранена в кеше')
        return response

    async def get_member_in_room(self, room_id: UUID) -> list[RoomMemberDtoGet]:
        """Получить участников комнаты"""
        async with self._uow as uow:
            list_room_member_orm = await uow.room_repo.get_member_in_room(room_id)
            response = [
                RoomMemberDtoGet(**room_orm.to_dict())
                for room_orm in list_room_member_orm
            ]
            return response

    async def add_member_in_room(self, member: RoomMemberDtoSave) -> RoomMemberDtoGet:
        """Добавить нового участника в комнату"""
        async with self._uow as uow:
            room_member_orm = await uow.room_repo.add_member_in_room(member)
            self.log_info(f'Пользователь {member.user_id} успешно добавлен в комнату {room_member_orm.room_id}')
            response = RoomMemberDtoGet(**room_member_orm.to_dict())
            if _get_config().mode not in (AppMode.DEV,):
                uow.add_event(
                    event_name='Add new member in room',
                    payload=response.model_dump(),
                    event_type=EventType.ADD_MEMBER_IN_ROOM
                )
                self.log_info(f'Событие {EventType.ADD_MEMBER_IN_ROOM} зарегистрировано')
            return response

    async def remove_member_in_room(self, room_id: UUID, user_id: str) -> RoomMemberDtoGet:
        """Удалить участника из комнаты"""
        async with self._uow as uow:
            room_member_orm = await uow.room_repo.remove_member_in_room(room_id, user_id)
            self.log_info(f'Пользователь {user_id} успешно удален из комнаты {room_id}')
            response = RoomMemberDtoGet(**room_member_orm.to_dict())
            if _get_config().mode not in (AppMode.DEV,):
                uow.add_event(
                    event_name='Remove member in room',
                    payload=response.model_dump(),
                    event_type=EventType.REMOVE_MEMBER_IN_ROOM
                )
                self.log_info(f'Событие {EventType.REMOVE_MEMBER_IN_ROOM} зарегистрировано')
            return response

    async def delete_room(self, room_id: UUID) -> RoomDtoGet:
        """Удалить информацию о комнате"""
        async with self._uow as uow:
            room_orm = await uow.room_repo.delete(room_id)
            self.log_info(f'Комната была удалена {room_id}')
            response = RoomDtoGet(**room_orm.to_dict())
            if _get_config().mode not in (AppMode.DEV,):
                uow.add_event(
                    event_name='Remove room',
                    payload=response.model_dump(),
                    event_type=EventType.DELETE_ROOM
                )
                self.log_info(f'Событие {EventType.DELETE_ROOM} зарегистрировано')
        is_saved = await self._cache.delete_room_info(room_id)
        if not is_saved:
            self.log_warning(f'Комната {room_id} не была сохранена в кеше')
        return response