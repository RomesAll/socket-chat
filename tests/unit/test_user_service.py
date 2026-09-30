from datetime import datetime, timezone
from unittest.mock import AsyncMock
from app.business_logic.psw_manager import PasswordManager
from app.business_logic.services.user_service import UserService
import pytest
from app.data_layer.models import User, UserInfo, RoleEnum
from app.shared.dto import UserDtoUpdateDefaultInfo


@pytest.mark.asyncio
async def test_add_user(uow_mock, default_user_orm, save_user_dto):
    """Тест для сохранения нового пользователя с помощью mock"""
    uow_mock.user_repo.save.return_value = default_user_orm

    verify_code_storage = AsyncMock()
    cache = AsyncMock()
    cache.save_user_info.return_value = True

    user_dto_result = await UserService(
        uow=uow_mock,
        verify_code_storage=verify_code_storage,
        psw_manager=PasswordManager,
        cache=cache
    ).add_user(new_user=save_user_dto)

    cache.save_user_info.assert_called_once()
    uow_mock.user_repo.save.assert_called_once()

    assert user_dto_result.id == save_user_dto.id
    assert user_dto_result.user_info.email == save_user_dto.user_info.email


@pytest.mark.asyncio
async def test_get_users_brief_info(uow_mock, default_user_orm):
    """Тест для получения краткой информации о пользователе с помощью mock"""
    uow_mock.user_repo.get_users.return_value = [default_user_orm, ]

    verify_code_storage = AsyncMock()
    cache = AsyncMock()

    user_dto_result = await UserService(
        uow=uow_mock,
        verify_code_storage=verify_code_storage,
        psw_manager=PasswordManager,
        cache=cache
    ).get_users_brief_info(limit=1, offset=0)

    uow_mock.user_repo.get_users.assert_called_once()
    assert user_dto_result[0].id == default_user_orm.id


@pytest.mark.asyncio
async def test_get_users_extension_info(uow_mock, default_user_orm):
    """Тест для получения расширенной информации о пользователе с помощью mock"""
    uow_mock.user_repo.get_users.return_value = [default_user_orm, ]

    verify_code_storage = AsyncMock()
    cache = AsyncMock()

    user_dto_result = await UserService(
        uow=uow_mock,
        verify_code_storage=verify_code_storage,
        psw_manager=PasswordManager,
        cache=cache
    ).get_users_ext_info(limit=1, offset=0)

    uow_mock.user_repo.get_users.assert_called_once()
    assert user_dto_result[0].id == default_user_orm.id
    assert hasattr(user_dto_result[0], 'email')


@pytest.mark.asyncio
async def test_update_user(uow_mock, save_user_dto, default_user_orm):
    """Тест для обновления информации о пользователе"""
    default_user_orm.display_name = 'Катя'
    uow_mock.user_repo.update_default_info.return_value = default_user_orm

    verify_code_storage = AsyncMock()
    cache = AsyncMock()

    user_dto_result = await UserService(
        uow=uow_mock,
        verify_code_storage=verify_code_storage,
        psw_manager=PasswordManager,
        cache=cache
    ).update_default_info_user(
        user_id=default_user_orm.id,
        update_user=UserDtoUpdateDefaultInfo(display_name='Катя')
    )
    cache.save_user_info.assert_called_once()
    uow_mock.user_repo.update_default_info.assert_called_once()
    assert user_dto_result.display_name == 'Катя'