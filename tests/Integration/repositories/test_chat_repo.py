from uuid import uuid4
import pytest
from app.data_layer.exceptions import RecordNotFound
from app.shared.dto import ChatDtoSave, ChatDtoUpdate, ChatMemberDtoSave


@pytest.mark.asyncio
async def test_get_by_id_success(chat_repo, default_chat):
    """Тест получение пользователя по id"""
    chat = await chat_repo.get_chat_by_id(default_chat.id)
    assert chat.id == default_chat.id


@pytest.mark.asyncio
async def test_get_by_id_not_found(chat_repo):
    """Тест получение несуществующего пользователя по id"""
    random_id = uuid4()
    with pytest.raises(RecordNotFound) as exc_info:
        await chat_repo.get_chat_by_id(random_id)
    assert str(exc_info.value) == f'Ошибка бд, причина: Не удалось найти запись id={random_id} в таблице chat'


@pytest.mark.asyncio
async def test_save(chat_repo, default_room, default_user):
    """Тест получение пользователей"""
    chat_id = uuid4()
    request = ChatDtoSave(
        id=chat_id,
        name='chat1',
        room_id=default_room.id,
        members=[ChatMemberDtoSave(chat_id=chat_id, user_id=default_user.id)]
    )
    chat = await chat_repo.save(request)
    assert chat.id == request.id
    assert chat.name == request.name
    assert len(chat.members) == 1


@pytest.mark.asyncio
async def test_update_success(chat_repo, default_chat):
    """Тест получение пользователей"""
    chat_name = 'UpdateChat'
    update_data = ChatDtoUpdate(
        name=chat_name,
    )
    chat = await chat_repo.update(default_chat.id, update_data)
    assert chat.name == chat_name


async def test_delete_success(chat_repo, default_room, default_user):
    """Тест получение пользователей"""
    chat_id = uuid4()
    new_chat = ChatDtoSave(
        id=chat_id,
        name='chat1',
        room_id=default_room.id,
        members=[ChatMemberDtoSave(chat_id=chat_id, user_id=default_user.id)]
    )
    chat = await chat_repo.save(new_chat)
    delete_chat = await chat_repo.delete(chat.id)
    assert delete_chat.id == chat_id