from uuid import uuid4
import pytest
from app.business_logic.jwt_manager import JWTAccessManager, JWTRefreshManager
from app.data_layer.models import RoleEnum
from app.shared.dto.jwt import JWTAccessToken, JWTRefreshToken


@pytest.mark.asyncio
def test_access_token():
    """Тест создания и декодирования access токена"""
    request = JWTAccessToken(
        user_id='RomeSky',
        sub='Роман',
        exp=1000,
        session_id=uuid4(),
        role=RoleEnum.DEFAULT_USER
    )
    token = JWTAccessManager.create_token(request)
    payload = JWTAccessManager.decode_token(token)
    assert payload.user_id == request.user_id
    assert payload.sub == request.sub
    assert payload.role == request.role
    assert payload.session_id == request.session_id


@pytest.mark.asyncio
def test_refresh_token():
    """Тест создания и декодирования refresh токена"""
    request = JWTRefreshToken(
        user_id='RomeSky',
        sub='Роман',
        exp=1000,
        session_id=uuid4(),
        role=RoleEnum.DEFAULT_USER,
        refresh_id=uuid4()
    )
    token = JWTRefreshManager.create_token(request)
    payload = JWTRefreshManager.decode_token(token)
    assert payload.user_id == request.user_id
    assert payload.sub == request.sub
    assert payload.role == request.role
    assert payload.session_id == request.session_id
    assert payload.refresh_id == request.refresh_id