from uuid import uuid4
import pytest
from app.data_layer.exceptions import RecordNotFound
from app.shared.dto import RoomDtoUpdate, RoomDtoSave, RoomMemberDtoSave
from contextlib import nullcontext


@pytest.mark.asyncio
async def test_get_by_id_success(room_repo, default_room):
    """Тест для получения комнаты по id"""
    room = await room_repo.get_room_by_id(default_room.id)
    assert room.id == default_room.id
    assert room.name == default_room.name


@pytest.mark.asyncio
async def test_get_by_id_not_found(room_repo):
    """Тест для получения несуществующей комнаты по id"""
    random_id = uuid4()
    with pytest.raises(RecordNotFound) as exc_info:
        await room_repo.get_room_by_id(random_id)
    assert str(exc_info.value) == f'Ошибка бд, причина: Не удалось найти запись id={random_id} в таблице room'


@pytest.mark.asyncio
async def test_get_success(room_repo, default_room):
    """Тест для получения комнаты"""
    rooms = await room_repo.get_rooms(limit=1, offset=0)
    assert type(rooms) == list
    assert len(rooms) == 1
    assert rooms[-1].id == default_room.id


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "name, expected_context",
    [
        ("Room1", nullcontext()),
        ("Room2", nullcontext()),
    ],
)
async def test_save(room_repo, default_user, name, expected_context):
    """Тест для сохранения сообщения"""
    room_id = uuid4()
    request = RoomDtoSave(
        id=room_id,
        name=name,
        members=[RoomMemberDtoSave(
            room_id=room_id,
            user_id=default_user.id
        )],
        owner_id=default_user.id,
    )
    with expected_context:
        room = await room_repo.save(request)
        assert room.id == room_id
        assert room.name == name
        assert default_user.id == room.members[0].user_id


@pytest.mark.asyncio
async def test_update_success(room_repo, default_room):
    """Тест для обновления сообщения"""
    room_name = 'UpdateRoom'
    update_data = RoomDtoUpdate(
        name=room_name
    )
    room = await room_repo.update_room(default_room.id, update_data)
    assert room.name == room_name


async def test_delete_success(room_repo, default_room, default_user):
    """Тест для удаления сообщения"""
    room_id = uuid4()
    new_room = RoomDtoSave(
        id=room_id,
        name='RoomTest',
        members=[RoomMemberDtoSave(
            room_id=room_id,
            user_id=default_user.id
        )],
        owner_id=default_user.id,
    )
    user = await room_repo.save(new_room)
    delete_room = await room_repo.delete(user.id)
    assert delete_room.id == user.id