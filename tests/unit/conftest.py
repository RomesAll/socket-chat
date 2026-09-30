from unittest.mock import AsyncMock
from uuid import uuid4
from app.business_logic.unit_of_work import UnitOfWork
import pytest
from app.data_layer.models import RoomRole, MessageType
from app.shared.dto import UserDtoSave, UserDtoInfoSave, RoomDtoSave, RoomMemberDtoSave, ChatDtoSave, ChatMemberDtoSave, \
    MessageDtoSave


@pytest.fixture(scope='function')
def uow_mock():
    """Фикстура для получения mock unit of work паттерна"""
    sql_session_mock = AsyncMock()
    mongo_session_mock = AsyncMock()
    uow = UnitOfWork(sql_session_mock, mongo_session_mock)
    uow.user_repo = AsyncMock()
    uow.chat_repo = AsyncMock()
    uow.room_repo = AsyncMock()
    uow.msg_repo = AsyncMock()
    return uow


@pytest.fixture(scope='function')
def save_user_dto(default_user_orm) -> UserDtoSave:
    """Фикстура для получения dto модели сохранение пользователя"""
    user_info = {
        **default_user_orm.user_info.to_dict(),
        'repeat_password': default_user_orm.user_info.password,
    }
    user_dto = UserDtoSave(
        **default_user_orm.to_dict(),
        user_info=UserDtoInfoSave(**user_info)
    )
    return user_dto


@pytest.fixture(scope='function')
def save_room_dto(default_room_orm, default_user_orm, default_chat_orm) -> RoomDtoSave:
    """Фикстура для получения dto модели сохранение комнаты"""
    room_dto = RoomDtoSave(
        id=default_room_orm.id,
        name=default_room_orm.name,
        description=default_room_orm.description,
        avatar_url=default_room_orm.avatar_url,
        owner_id=default_room_orm.owner_id,
        is_private=True,
        members=[RoomMemberDtoSave(
            user_id=default_user_orm.id,
            room_id=default_room_orm.id,
            role=RoomRole.OWNER
        )],
        chats=[ChatDtoSave(
            id=default_chat_orm.id,
            name=default_chat_orm.name,
            room_id=default_room_orm.id,
            members=[ChatMemberDtoSave(
                user_id=default_user_orm.id,
                chat_id=default_chat_orm.id,
            )],
        )]
    )
    return room_dto


@pytest.fixture(scope='function')
def save_msg_dto(default_message_orm) -> MessageDtoSave:
    msg_dto = MessageDtoSave(
        id=default_message_orm.id,
        chat_id=uuid4(),
        sender_id='Roman',
        body_encrypted='hello',
        type=MessageType.TEXT
    )
    return msg_dto