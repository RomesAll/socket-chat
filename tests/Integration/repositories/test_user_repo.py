import pytest
from app.data_layer.exceptions import RecordNotFound
from app.shared.dto import UserDtoSave, UserDtoInfoSave, UserDtoUpdateDefaultInfo
from contextlib import nullcontext


@pytest.mark.asyncio
async def test_get_by_id_success(user_repo, default_user):
    """Тест для получения пользователя по id"""
    user = await user_repo.get_user_by_id(default_user.id)
    assert user.id == default_user.id
    assert user.display_name == default_user.display_name


@pytest.mark.asyncio
async def test_get_by_id_not_found(user_repo):
    """Тест для получения несуществующего пользователя по id"""
    random_id = 'User1'
    with pytest.raises(RecordNotFound) as exc_info:
        await user_repo.get_user_by_id(random_id)
    assert str(exc_info.value) == f'Ошибка бд, причина: Не удалось найти запись id={random_id} в таблице user'


@pytest.mark.asyncio
async def test_get_success(user_repo, default_user):
    """Тест для получения пользователей"""
    users = await user_repo.get_users(limit=1, offset=0)
    assert type(users) == list
    assert len(users) == 1
    assert users[-1].id == default_user.id


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "user_id, display_name, years_old, email, password, expected_context",
    [
        ("RomanId", "Рома", "18", "rom@gmail.com", "1", nullcontext()),
        ("NikitaId", "Никита", "18", "nikita@gmail.com", "1", nullcontext()),
        ("SashaId", "Саша", "18", "sasha@gmail.com", "1", nullcontext()),
        ("RomanId", "Рома", "18", "rom1@gmail.com", "1", nullcontext()),
        ("Roman1Id", "Рома", "18", "rom@gmail.com", "1", nullcontext()),
    ]
)
async def test_save(user_repo, user_id, display_name, years_old, email, password, expected_context):
    """Тест для сохранения пользователей"""
    request = UserDtoSave(
        id=user_id,
        display_name=display_name,
        user_info=UserDtoInfoSave(
            id=user_id,
            years_old=int(years_old),
            email=email,
            password=password.encode(),
            repeat_password=password.encode()
        )
    )
    with expected_context:
        user = await user_repo.save(request)
        assert user.id == user_id
        assert user.display_name == display_name
        assert user.user_info.email == email


@pytest.mark.asyncio
async def test_update_success(user_repo, default_user):
    """Тест для обновления пользователей"""
    display_name = 'update'
    avatar_url = '/home/1.txt'
    update_data = UserDtoUpdateDefaultInfo(
        display_name=display_name,
        avatar_url=avatar_url
    )
    user = await user_repo.update_default_info(default_user.id, update_data)
    assert user.display_name == display_name
    assert user.avatar_url == avatar_url


async def test_delete_success(user_repo):
    """Тест для удаления пользователей"""
    new_user = UserDtoSave(
        id='Petr',
        display_name='Петр',
        user_info=UserDtoInfoSave(
            id='Petr',
            years_old=14,
            email='asdf@gmail.com',
            password=b'1',
            repeat_password=b'1'
        )
    )
    user = await user_repo.save(new_user)
    delete_user = await user_repo.delete(user.id)
    assert delete_user.id == user.id