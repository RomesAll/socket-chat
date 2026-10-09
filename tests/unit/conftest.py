from uuid import uuid4
import pytest
from app.data_layer.models import Chat, Room


@pytest.fixture(scope='function')
async def add_private_chat(db_session) -> Chat:
    new_chat = Chat(id=uuid4(), type='private')
    db_session.add(new_chat)
    await db_session.commit()
    return new_chat


@pytest.fixture(scope='function')
async def add_room(db_session, add_private_chat) -> Room:
    new_room = Room(chat_id=add_private_chat.id, name='Тестовая комната')
    db_session.add(new_room)
    await db_session.commit()
    return new_room