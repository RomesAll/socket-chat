from app.infrastructure.redis.verify_code_storage import VerifyCodeStorage


async def test_save_verify_code(redis_client):
    """Тест для сохранения и получения кода подтверждения"""
    user_id = 'Roman'
    code = 1234567
    storage = VerifyCodeStorage(redis_client, 10)
    await storage.save(user_id, code)
    assert await storage.validate_code(user_id, code)
    assert not await storage.validate_code(user_id, 321)