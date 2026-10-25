from uuid import uuid4
from app.shared.dto.enums import RoleEnum


async def test_jwt_facade_create_token(jwt_facade):
    """Тест: Создание пары access и refresh токенов."""
    tokens = jwt_facade.create_tokens(
        user_id='user_id',
        sub='some info',
        role=RoleEnum.ADMIN,
        refresh_id=uuid4()
    )
    assert len(tokens.access_token) > 0
    assert len(tokens.refresh_token) > 0


async def test_jwt_decode_access_token_success(jwt_facade):
    """Тест: Успешное декодирование access токена."""
    tokens = jwt_facade.create_tokens(
        user_id='user_id',
        sub='some info',
        role=RoleEnum.ADMIN,
        refresh_id=uuid4()
    )
    payload = jwt_facade.jwt_access_manager.decode_token(tokens.access_token)

    assert payload.user_id == 'user_id'
    assert payload.sub == 'some info'
    assert payload.role == RoleEnum.ADMIN


async def test_jwt_decode_refresh_token_success(jwt_facade):
    """Тест: Успешное декодирование refresh токена."""
    tokens = jwt_facade.create_tokens(
        user_id='user_id',
        sub='some info',
        role=RoleEnum.ADMIN,
        refresh_id=uuid4()
    )
    payload = jwt_facade.jwt_refresh_manager.decode_token(tokens.refresh_token)

    assert payload.user_id == 'user_id'
    assert payload.sub == 'some info'
    assert payload.role == RoleEnum.ADMIN