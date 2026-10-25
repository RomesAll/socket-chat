from dataclasses import asdict
from uuid import UUID
from app.business_logic.mappers.room_mapper import RoomMapper
from app.business_logic.unit_of_work import UnitOfWork
from app.domain.events import RoomCreated, RoomUpdated, RoomDeleted
from app.infrastructure.redis import RoomCache
from app.shared.dto.base import UNSET
from app.shared.dto.enums import ChatRole
from app.shared.dto.room import (
    RoomSaveDTO,
    RoomDTO,
    RoomUpdateDTO,
    RoomUserMemberDTO, TopRoomsByMemberDTO,
)
from app.shared.log_config import LogMixin


class RoomService(LogMixin):
    """Сервис для управления комнатами."""

    def __init__(self, uow: UnitOfWork, mapper: RoomMapper, cache: RoomCache):
        self._uow = uow
        self._mapper = mapper
        self._cache = cache

    async def get_room_members(self, room_id: UUID):
        return await self._uow.room_read_repo.get_room_members(room_id)

    async def get(self, room_id: UUID) -> RoomDTO:
        """
        Получить информацию о комнате по ID.
        :exception RecordNotFound если не найдена запись.
        """
        cached = await self._cache.get_default(room_id)
        if cached:
            return cached
        room_orm = await self._uow.room_repo.get_record_by_id(room_id)
        room_dto = self._mapper.to_dto(room_orm)
        self._uow.add_after_commit(lambda : self._cache.save_default(room_dto))
        return room_dto

    async def get_top_rooms_by_member(self, top_count: int = 5) -> list[TopRoomsByMemberDTO]:
        """Поучить список комнат по наибольшему кол-ву участников"""
        return await self._uow.room_read_repo.top_rooms_by_member(top_count)

    async def find(self, room_id: UUID) -> RoomDTO | None:
        """Найти комнату по ID. Вернет None, если не найдена."""
        cached = await self._cache.get_default(room_id)
        if cached:
            return cached
        result = await self._uow.room_read_repo.get_by_id(room_id)
        if result:
            self._uow.add_after_commit(lambda: self._cache.save_default(result))
        return result

    async def get_many(self, limit: int, offset: int) -> list[RoomDTO]:
        """Получить комнаты с пагинацией."""
        rooms_orm = await self._uow.room_repo.get_records(limit, offset)
        return [self._mapper.to_dto(room) for room in rooms_orm]

    async def get_user_rooms(self, user_id: str) -> list[RoomUserMemberDTO]:
        """Получить комнаты пользователя с ролью и количеством участников."""
        return await self._uow.room_read_repo.get_user_rooms(user_id)

    async def get_owner_rooms_with_members(
        self, owner_id: str,
    ) -> tuple[list[UUID], dict[UUID, list[tuple[str, ChatRole]]]]:
        """Получить id комнат владельца и участников этих комнат."""
        return await self._uow.room_read_repo.get_owner_rooms_with_members(owner_id)

    async def get_owner_room(self, room_id: UUID) -> str | None:
        """Получить id владельца комнаты или None."""
        return await self._uow.room_read_repo.get_owner_room(room_id)

    async def is_member(self, room_id: UUID, user_id: str) -> bool:
        """Является ли пользователь участником комнаты."""
        return await self._uow.room_read_repo.is_member(room_id, user_id)

    async def save(self, room_dto: RoomSaveDTO) -> RoomDTO:
        """Сохранить информацию о комнате."""
        room_orm = await self._uow.room_repo.save(room_dto)
        saved_room = self._mapper.to_dto(room_orm)
        self._uow.add_event(RoomCreated(
            room=saved_room
        ))
        self.log_info(f"Создана комната {saved_room.chat_id}")
        return saved_room

    async def update(self, room_id: UUID, room_dto: RoomUpdateDTO) -> RoomDTO:
        """Обновить информацию о комнате."""
        room_orm = await self._uow.room_repo.update(room_id, room_dto)
        updated_room = self._mapper.to_dto(room_orm)
        self._uow.add_event(RoomUpdated(
            room=updated_room,
            changed_fields=[
                key for key, value in asdict(room_dto).items()
                if type(value) is not UNSET
            ]
        ))
        self.log_info(f"Обновлена комната {updated_room.chat_id}")
        return updated_room

    async def delete(self, room_id: UUID) -> RoomDTO:
        """Удалить комнату."""
        room_orm = await self._uow.room_repo.delete(room_id)
        deleted_room = self._mapper.to_dto(room_orm)
        self._uow.add_event(RoomDeleted(
            room_id=room_id
        ))
        self.log_info(f"Удалена комната {deleted_room.chat_id}")
        return deleted_room