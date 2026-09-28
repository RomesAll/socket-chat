from unittest.mock import AsyncMock
from app.business_logic.unit_of_work import UnitOfWork
import pytest
from app.shared.dto import UserDtoSave, UserDtoInfoSave


@pytest.fixture(scope='function')
def uow_mock():
    sql_session_mock = AsyncMock()
    mongo_session_mock = AsyncMock()
    uow = UnitOfWork(sql_session_mock, mongo_session_mock)
    uow.user_repo = AsyncMock()
    uow.chat_repo = AsyncMock()
    uow.room_repo = AsyncMock()
    uow.msg_repo = AsyncMock()
    return uow


@pytest.fixture(scope='function')
def new_user_dto():
    new_user_dto = UserDtoSave(
        id='RomanId',
        display_name='Роман',
        user_info=UserDtoInfoSave(
            id='RomanId',
            years_old=12,
            email='rome@gmail.com',
            password=b'1',
            repeat_password=b'1'
        )
    )
    return new_user_dto