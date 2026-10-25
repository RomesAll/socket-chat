from redis.asyncio import Redis


class RedisClient:
    """Клиент Redis, хранить подключение к Redis серверу."""

    def __init__(self, uri: str, max_connections: int = 100):
        self._client = Redis.from_url(uri, max_connections=max_connections)

    @property
    def client(self) -> Redis:
        return self._client

    async def ping(self) -> bool:
        """Проверить активность подключения к БД."""
        try:
            return await self._client.ping()
        except Exception:
            return False

    async def close(self) -> None:
        """Закрыть пул соединений."""
        await self._client.close()