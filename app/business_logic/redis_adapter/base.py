from typing import Self
import redis
from redis.asyncio import *
from functools import wraps


class BaseRedisAdapter:
    """Базовый класс адаптер для redis"""
    def __init__(self, url: str):
        self.url = url
        self._client: Redis | None = None

    async def connection(self) -> Self:
        """Создание подключения к redis"""
        if not self._client:
            try:
                self._client = from_url(self.url)
                await self._client.ping()
            except (redis.exceptions.ConnectionError, ValueError) as e:
                self._client = None
                raise e
        return self

    async def close(self) -> Self:
        """Отключение от redis сервера"""
        if self._client:
            await self._client.close()
            self._client = None
        return self

    @property
    def client(self) -> Redis:
        """Получение клиента"""
        if not self._client:
            raise RuntimeError("Redis client не инициализирован. Сначала вызовите connect()")
        return self._client

