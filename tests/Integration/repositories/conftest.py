import pytest
from app.data_layer.repositories import (
    UserRepository,
    ChatRepository,
    RoomRepository,
    MessageRepository
)


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


