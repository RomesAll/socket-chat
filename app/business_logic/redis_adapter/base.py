from redis.asyncio import Redis
from threading import Lock


class RedisConnectionSingleton(type):
    """
    Паттерн Singleton (потокобезопасный) для создания одиночек
    """
    _instances = {}
    _lock = Lock()

    def __call__(cls, *args, **kwargs):
        with cls._lock:
            if cls not in cls._instances:
                cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


class RedisConnection(metaclass=RedisConnectionSingleton):
    """
    Класс создания подключения к redis серверу
    """
    _client: Redis | None = None

    async def connection(self, url: str) -> Redis:
        if self._client is None:
            client = Redis.from_url(url)
            await client.ping()
            self._client = client
        return self._client

    async def close(self) -> None:
        if self._client:
            await self._client.close()
            self._client = None

    @property
    def client(self) -> Redis:
        if self._client is None:
            raise RuntimeError("Redis client не инициализирован")
        return self._client