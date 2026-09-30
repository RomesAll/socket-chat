import pytest_asyncio
from redis.asyncio import Redis


@pytest_asyncio.fixture(scope='session', loop_scope='session')
async def redis_client(config):
    client = Redis.from_url(config.redis.url)
    yield client
    await client.close()