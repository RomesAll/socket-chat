from typing import Sequence
from uuid import UUID
from sqlalchemy import select, and_
from app.business_logic.exceptions import OwnerInRoomEmpty
from app.data_layer.exceptions import RecordNotFound
from app.data_layer.repositories.base.base_repo import (
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

    async def change_owner(self, room_id: UUID, new_owner: str) -> Room:
        """
        Сменить владельца для комнаты в базе данных.

        :param room_id: Идентификатор комнаты.
        :param new_owner: ID нового владельца.
        :return: Обновленная ORM-модель Room в сессии.
        """
        room_info = await self.get_record_by_id(room_id)
        room_info.owner_id = new_owner
        await self.session.flush()
        return room_info