from uuid import uuid4
from app.infrastructure.security.jwt_manager import JWTFacade, JWTAccessManager, JWTRefreshManager
from app.shared.dto.enums import RoleEnum


async def test_jwt_facade_create_token():
    """Тест: Создание пары access и refresh токенов."""
    tokens = JWTFacade.create_tokens(
        user_id='user_id',
        sub='some info',
        role=RoleEnum.ADMIN,
        refresh_id=uuid4()
    )
    assert len(tokens.access_token) == 275
    assert len(tokens.refresh_token) == 345


async def test_jwt_decode_access_token_success():
    """Тест: Успешное декодирование access токена."""
    tokens = JWTFacade.create_tokens(
        user_id='user_id',
        sub='some info',
        role=RoleEnum.ADMIN,
        refresh_id=uuid4()
    )
    payload = JWTAccessManager.decode_token(tokens.access_token)

    assert payload.user_id == 'user_id'
    assert payload.sub == 'some info'
    assert payload.role == RoleEnum.ADMIN


async def test_jwt_decode_refresh_token_success():
    """Тест: Успешное декодирование refresh токена."""
    tokens = JWTFacade.create_tokens(
        user_id='user_id',
        sub='some info',
        role=RoleEnum.ADMIN,
        refresh_id=uuid4()
    )
    payload = JWTRefreshManager.decode_token(tokens.refresh_token)

    assert payload.user_id == 'user_id'
    assert payload.sub == 'some info'
    assert payload.role == RoleEnum.ADMIN