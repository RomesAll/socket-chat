import asyncio
from uuid import uuid4
import pytest
from app.business_logic.redis_adapter import JWTWhiteListCache


@pytest.mark.asyncio
async def test_save_refresh_token(redis_client):
    """Тест для сохранения и получения id refresh токена в redis"""
    user_id = 'Roman'
    token_id = uuid4()
    white_list = JWTWhiteListCache(redis_client)
    is_saved = await white_list.save_refresh_token(user_id=user_id, token_id=token_id, ex=1)
    assert is_saved
    assert await white_list.is_token_active(user_id, token_id)
    await asyncio.sleep(1)
    assert not await white_list.is_token_active(user_id, token_id)

