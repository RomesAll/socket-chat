from uuid import uuid4
from app.data_layer.models import User, UserInfo, Chat, Room, ChatMember, Message, MessageType
from app.data_layer.repositories import (
    UserRepository,
    ChatRepository,
    RoomRepository,
    MessageRepository
)
import pytest


@pytest.fixture(scope='function')
def user_repo(sql_session):
    """Фикстура для получения user репозитория с асинхронной сессией"""
    return UserRepository(sql_session)


@pytest.fixture(scope='function')
def chat_repo(sql_session):
    """Фикстура для получения chat репозитория с асинхронной сессией"""
    return ChatRepository(sql_session)


@pytest.fixture(scope='function')
def room_repo(sql_session):
    """Фикстура для получения room репозитория с асинхронной сессией"""
    return RoomRepository(sql_session)


@pytest.fixture(scope='function')
def message_repo(sql_session):
    """Фикстура для получения message репозитория с асинхронной сессией"""
    return MessageRepository(sql_session)


@pytest.fixture(scope='function')
async def default_user(sql_session) -> User:
    """Фикстура для добавления базового пользователя в сессию"""
    user = User(
        id='RomanSky',
        display_name='Роман',
        user_info=UserInfo(
            id='RomanSky',
            email='romesky@gmail.com',
            password=b'hello',
        )
    )
    sql_session.add(user)
    await sql_session.flush()
    return user


@pytest.fixture(scope='function')
async def default_chat(sql_session, default_user) -> Chat:
    """Фикстура для добавления базового чата в сессию"""
    chat_id = uuid4()
    chat = Chat(
        id=chat_id,
        name='TestChat',
        members=[ChatMember(
            chat_id=chat_id,
            user_id=default_user.id
        )]
    )
    sql_session.add(chat)
    await sql_session.flush()
    return chat


@pytest.fixture(scope='function')
async def default_room(sql_session, default_user) -> Room:
    """Фикстура для добавления базовой комнаты в сессию"""
    room_id = uuid4()
    room = Room(
        id=room_id,
        name='TestRoom',
        description='',
        owner_id=default_user.id,
    )
    sql_session.add(room)
    return room


@pytest.fixture(scope='function')
async def default_message(sql_session, default_user, default_chat) -> Message:
    """Фикстура для добавления базового сообщения в сессию"""
    message_id = uuid4()
    message = Message(
        id=message_id,
        chat_id=default_chat.id,
        sender_id=default_user.id,
        body_encrypted='hello world',
        type=MessageType.TEXT,
    )
    sql_session.add(message)
    return message
