from uuid import uuid4
import pytest
from app.business_logic.redis_adapter import SessionKeyStorage


@pytest.mark.asyncio
async def test_save_session_key(redis_client):
    """Тест для сохранения и получения сессионного ключа в redis"""
    user_id = 'Roman'
    session_id = uuid4()
    storage = SessionKeyStorage(redis_client)
    is_saved = await storage.save(user_id, session_id, b'session_key_1234')
    assert is_saved
    session_key = await storage.get(user_id, session_id)
    assert session_key == b'session_key_1234'