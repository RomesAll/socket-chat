from app.shared.config import create_config, AppMode
from redis.asyncio import Redis
import pytest

config = create_config(mode=AppMode.TEST)


@pytest.fixture(scope='session')
def redis_client():
    client = Redis.from_url(url=config.redis.url)
    return client