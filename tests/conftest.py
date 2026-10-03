from datetime import datetime, timezone
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.data_layer.models import (
    User, UserInfo, Chat, ChatMember, Room, Message,
    MessageType, RoleEnum, RoomMember, RoomRole,
)
from app.shared.config import create_config, AppMode


# ---------- engine / session ----------

@pytest.fixture(scope='session')
def config():
    return create_config(mode=AppMode.TEST)


@pytest_asyncio.fixture(scope='session', loop_scope='session')
async def async_engine(config):
    engine = create_async_engine(config.postgres.url, echo=False)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture(scope='session', autouse=True, loop_scope='session')
async def setup_db(async_engine):
    """Один раз на сессию создаём таблицы, в конце — дропаем."""
    from app.data_layer.models import Base  # подставь свой Base, если импорт другой
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield

    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def sql_session(async_engine):
    """Сессия на тест, rollback в конце."""
    session_factory = async_sessionmaker(bind=async_engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session
        await session.rollback()


# ---------- ORM-шаблоны (только данные, без сессии) ----------

@pytest.fixture
def default_user_orm():
    now = datetime.now(tz=timezone.utc)
    return User(
        id='RomanSky',
        display_name='Роман',
        user_info=UserInfo(
            id='RomanSky',
            email='romesky@gmail.com',
            password=b'hello',
            created_at=now,
            updated_at=now,
            role=RoleEnum.DEFAULT_USER,
        ),
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
def default_room_orm(default_user_orm) -> Room:
    now = datetime.now(tz=timezone.utc)
    room_id = uuid4()
    return Room(
        id=room_id,
        name='TestRoom',
        description='',
        owner_id=default_user_orm.id,
        owner=default_user_orm,
        is_private=True,
        members=[
            RoomMember(
                room_id=room_id,
                user_id=default_user_orm.id,
                role=RoomRole.OWNER,
                created_at=now,
                updated_at=now,
            )
        ],
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
def default_chat_orm(default_user_orm, default_room_orm) -> Chat:
    now = datetime.now(tz=timezone.utc)
    chat_id = uuid4()
    return Chat(
        id=chat_id,
        room_id=default_room_orm.id,
        name='TestChat',
        members=[
            ChatMember(
                chat_id=chat_id,
                user_id=default_user_orm.id,
                created_at=now,
                updated_at=now,
            )
        ],
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
def default_message_orm(default_user_orm, default_chat_orm) -> Message:
    now = datetime.now(tz=timezone.utc)
    return Message(
        id=uuid4(),
        chat_id=default_chat_orm.id,
        sender_id=default_user_orm.id,
        body_encrypted='hello world',
        type=MessageType.TEXT,
        created_at=now,
        updated_at=now,
        is_edited=False,
        is_deleted=False,
    )


# ---------- "в сессии": добавляем в БД с правильным порядком ----------

@pytest_asyncio.fixture
async def default_user_in_session(sql_session, default_user_orm) -> User:
    sql_session.add(default_user_orm)
    await sql_session.flush()
    return default_user_orm


@pytest_asyncio.fixture
async def default_room_in_session(sql_session, default_room_orm) -> Room:
    sql_session.add(default_room_orm)
    await sql_session.flush()
    return default_room_orm


@pytest_asyncio.fixture
async def default_chat_in_session(
    sql_session,
    default_chat_orm,
    default_room_in_session,   # room должен быть в БД ДО chat
) -> Chat:
    sql_session.add(default_chat_orm)
    await sql_session.flush()
    return default_chat_orm


@pytest_asyncio.fixture
async def default_message_in_session(
    sql_session,
    default_message_orm,
    default_user_in_session,   # user в БД
    default_chat_in_session,   # chat в БД
) -> Message:
    sql_session.add(default_message_orm)
    await sql_session.flush()
    return default_message_orm