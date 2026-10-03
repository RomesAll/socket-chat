from app.data_layer.models import Base
from app.data_layer.repositories import (
    UserRepository,
    ChatRepository,
    RoomRepository,
    MessageRepository
)
import pytest
import pytest_asyncio


@pytest_asyncio.fixture(scope='session', autouse=True, loop_scope='session')
async def setup_db(async_engine):
    """
    Глобальная фикстура: срабатывает один раз при старте тестов.
    Создает таблицы в базе данных
    """
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


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
