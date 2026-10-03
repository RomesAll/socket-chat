import pytest
from app.business_logic.redis_adapter import VerifyCodeStorage


@pytest.mark.asyncio
async def test_save_verify_code(redis_client):
    """Тест для сохранения и получения кода подтверждения"""
    user_id = 'Roman'
    code = 1234567
    storage = VerifyCodeStorage(redis_client)
    await storage.save(user_id, code)
    assert await storage.validate_code(user_id, code)
    assert not await storage.validate_code(user_id, 321)