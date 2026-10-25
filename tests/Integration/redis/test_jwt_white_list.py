from uuid import uuid4
from app.infrastructure.redis.jwt_white_list import JWTWhiteListCache


async def test_save_refresh_token(redis_client):
    """Тест для сохранения и получения id refresh токена в redis"""
    user_id = 'Roman'
    token_id = uuid4()
    white_list = JWTWhiteListCache(redis_client)
    is_saved = await white_list.save_refresh_token(user_id=user_id, token_id=token_id, ex=1)
    assert is_saved
    assert await white_list.is_token_active(user_id, token_id)

