import datetime
from datetime import date
from uuid import uuid4
import pytest
from app.data_layer.models import MessageType
from app.shared.dto import MessageDtoSave, MessageDtoUpdate


@pytest.mark.asyncio
async def test_get_by_chat_id_success(message_repo, default_message):
    """Тест получение пользователя по id"""
    msg = await message_repo.get_message_by_chat(date_limit=date.today(), chat_id=default_message.chat_id)
    for c_msg in msg:
        assert c_msg.chat_id == default_message.chat_id


@pytest.mark.asyncio
async def test_save(message_repo, default_chat, default_user):
    """Тест получение пользователей"""
    msg_id = uuid4()
    request = MessageDtoSave(
        id=msg_id,
        chat_id=default_chat.id,
        sender_id=default_user.id,
        body_encrypted='hello',
        type=MessageType.TEXT,
    )
    msg = await message_repo.save(request)
    assert msg.id == msg_id
    assert msg.chat_id == request.chat_id


@pytest.mark.asyncio
async def test_update_success(message_repo, default_message):
    """Тест получение пользователей"""
    body_encrypted = 'UpdateMsg'
    update_data = MessageDtoUpdate(
        body_encrypted=body_encrypted,
        is_edited=True
    )
    msg = await message_repo.update(default_message.id, update_data)
    assert msg.id == default_message.id


async def test_delete_success(message_repo, default_room, default_chat, default_user):
    """Тест получение пользователей"""
    msg_id = uuid4()
    new_msg = MessageDtoSave(
        id=msg_id,
        chat_id=default_chat.id,
        sender_id=default_user.id,
        body_encrypted='hello',
        type=MessageType.TEXT,
    )
    msg = await message_repo.save(new_msg)
    delete_msg = await message_repo.delete(msg.id)
    assert delete_msg.id == new_msg.id