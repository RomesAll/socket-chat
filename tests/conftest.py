from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.data_layer.models import User, UserInfo, Chat, ChatMember, Room, Message, MessageType, RoleEnum, RoomMember, \
    RoomRole
from app.shared.config import create_config, AppMode
import pytest

config = create_config(mode=AppMode.TEST)


@pytest.fixture(scope='session')
async def async_engine():
    """
    Фикстура для создания пула соединений (асинхронного движка)
    на уровне всей сессии
    """
    engine = create_async_engine(config.postgres.url, echo=False)
    yield engine
    await engine.dispose()


@pytest.fixture(scope='function')
async def sql_session(async_engine):
    """
    Главная фикстура для тестов. Вызывается перед каждым тестом.
    Она отдает сессию и делает ROLLBACK в конце,
    чтобы тесты не влияли на тестовую бд
    """
    session_factory = async_sessionmaker(bind=async_engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session
        await session.rollback()


@pytest.fixture(scope='function')
def default_user_orm():
    """Фикстура для получения orm объекта пользователя"""
    user = User(
        id='RomanSky',
        display_name='Роман',
        user_info=UserInfo(
            id='RomanSky',
            email='romesky@gmail.com',
            password=b'hello',
            created_at=datetime.now(tz=timezone.utc),
            updated_at=datetime.now(tz=timezone.utc),
            role=RoleEnum.DEFAULT_USER
        ),
        created_at=datetime.now(tz=timezone.utc),
        updated_at=datetime.now(tz=timezone.utc)
    )
    return user

@pytest.fixture(scope='function')
def default_chat_orm(default_user_orm, default_room_orm) -> Chat:
    """Фикстура для получения orm объекта чата"""
    chat_id = uuid4()
    chat = Chat(
        id=chat_id,
        room_id=default_room_orm.id,
        name='TestChat',
        members=[ChatMember(
            chat_id=chat_id,
            user_id=default_user_orm.id
        )],
    )
    return chat


@pytest.fixture(scope='function')
async def default_room_orm(default_user_orm) -> Room:
    """Фикстура для получения orm объекта комнаты"""
    room_id = uuid4()
    chat_id = uuid4()
    room = Room(
        id=room_id,
        name='TestRoom',
        description='',
        owner_id=default_user_orm.id,
        owner=default_user_orm,
        is_private=True,
        chats=[
            Chat(
                id=chat_id,
                room_id=room_id,
                name='TestChat',
                members=[ChatMember(
                    chat_id=chat_id,
                    user_id=default_user_orm.id
                )],
                created_at=datetime.now(tz=timezone.utc),
                updated_at=datetime.now(tz=timezone.utc)
            )
        ],
        members=[
            RoomMember(
                room_id=room_id,
                user_id=default_user_orm.id,
                role=RoomRole.OWNER,
                created_at=datetime.now(tz=timezone.utc),
                updated_at=datetime.now(tz=timezone.utc)
            )
        ],
        created_at=datetime.now(tz=timezone.utc),
        updated_at=datetime.now(tz=timezone.utc)
    )
    return room


@pytest.fixture(scope='function')
async def default_message_orm(default_user_orm, default_chat_orm) -> Message:
    """Фикстура для получения orm объекта сообщения"""
    message_id = uuid4()
    message = Message(
        id=message_id,
        chat_id=default_chat_orm.id,
        sender_id=default_user_orm.id,
        body_encrypted='hello world',
        type=MessageType.TEXT,
        created_at=datetime.now(tz=timezone.utc),
        updated_at=datetime.now(tz=timezone.utc),
        is_edited=False,
        is_deleted=False
    )
    return message


@pytest.fixture(scope='function')
async def default_user_in_session(sql_session, default_user_orm) -> User:
    """Фикстура для добавления базового пользователя в сессию"""
    sql_session.add(default_user_orm)
    await sql_session.flush()
    return default_user_orm


@pytest.fixture(scope='function')
async def default_chat(sql_session, default_chat_orm) -> Chat:
    """Фикстура для добавления базового чата в сессию"""
    sql_session.add(default_chat_orm)
    await sql_session.flush()
    return default_chat_orm


@pytest.fixture(scope='function')
async def default_room(sql_session, default_room_orm) -> Room:
    """Фикстура для добавления базовой комнаты в сессию"""
    sql_session.add(default_room_orm)
    return default_room_orm


@pytest.fixture(scope='function')
async def default_message(sql_session, default_message_orm, default_user_orm, default_chat_orm) -> Message:
    """Фикстура для добавления базового сообщения в сессию"""
    sql_session.add(default_user_orm)
    sql_session.add(default_chat_orm)
    sql_session.add(default_message_orm)
    return default_message_orm