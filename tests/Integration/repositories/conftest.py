from app.data_layer.repositories import (
    UserRepository,
    ChatRepository,
    RoomRepository,
    MessageRepository
)
from alembic.config import Config, command
from app.shared.config import create_config, AppMode
import pytest

config = create_config(mode=AppMode.TEST)


@pytest.fixture(scope='session', autouse=True)
def migration_db():
    """
    Глобальная фикстура: срабатывает один раз при старте тестов.
    Накатывает миграции Alembic на тестовую БД перед тестами и откатывает после
    """
    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option('sqlalchemy.url', config.postgres.url)
    command.upgrade(alembic_cfg, 'head')
    yield
    command.downgrade(alembic_cfg, 'base')


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
