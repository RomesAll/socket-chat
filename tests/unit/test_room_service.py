from unittest.mock import AsyncMock
from app.business_logic.services.room_service import RoomService
import pytest


@pytest.mark.asyncio
async def test_save_room(uow_mock, save_room_dto, default_room_orm):
    """Тест сохранения новой комнаты"""
    uow_mock.room_repo.save.return_value = default_room_orm

    cache = AsyncMock()
    cache.save_room.return_value = True

    room_dto_result = await RoomService(
        uow=uow_mock,
        cache=cache
    ).add_room(save_room_dto)

    cache.save_room.assert_called_once()
    uow_mock.room_repo.save.assert_called_once()

    assert room_dto_result.id == save_room_dto.id

