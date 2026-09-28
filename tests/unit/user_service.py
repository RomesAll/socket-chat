from datetime import datetime, timezone
from unittest.mock import AsyncMock
from app.business_logic.psw_manager import PasswordManager
from app.business_logic.services.user_service import UserService
import pytest
from app.data_layer.models import User, UserInfo, RoleEnum


@pytest.mark.asyncio
async def test_add_user(uow_mock, new_user_dto):
    """Тест для сохранения нового пользователя с помощью mock"""
    uow_mock.user_repo.save.return_value = User(
        id=new_user_dto.id,
        display_name=new_user_dto.display_name,
        user_info=UserInfo(
            id=new_user_dto.id,
            years_old=new_user_dto.user_info.years_old,
            email=new_user_dto.user_info.email,
            password = new_user_dto.user_info.password,
            role = RoleEnum.DEFAULT_USER,
            created_at=datetime.now(tz=timezone.utc),
            updated_at=datetime.now(tz=timezone.utc)
        ),
        created_at=datetime.now(tz=timezone.utc),
        updated_at=datetime.now(tz=timezone.utc),
    )

    verify_code_storage = AsyncMock()
    cache = AsyncMock()

    user_dto_result = await UserService(
        uow=uow_mock,
        verify_code_storage=verify_code_storage,
        psw_manager=PasswordManager,
        cache=cache
    ).add_user(new_user=new_user_dto)

    assert user_dto_result.id == new_user_dto.id
    assert user_dto_result.email == new_user_dto.user_info.email