from typing import Self
from redis.asyncio import *
from functools import wraps
from redis.exceptions import ConnectionError, TimeoutError, AuthenticationError, ResponseError, DataError
from app.business_logic.exceptions import RedisConnectionError, AuthRedisError, ResponseRedisError, DataErrorRedis


class BaseRedisAdapter:
    """Базовый класс адаптер для redis"""
    def __init__(self, url: str):
        self.url = url
        self._client: Redis | None = None

    @staticmethod
    def exception_handler(generate_exc: bool = False):
        """Обработчик redis исключений"""
        def wrapper_func(func):
            @wraps(func)
            async def wrapper(self, *args, **kwargs):
                exc = None
                try:
                    result = func(self, *args, **kwargs)
                    return result
                except AuthenticationError as e:
                    exc = AuthRedisError(self.url, str(e))
                except ConnectionError as e:
                    exc = RedisConnectionError(self.url, str(e))
                except TimeoutError as e:
                    exc = RedisConnectionError(self.url, str(e))
                except ResponseError as e:
                    exc = ResponseRedisError(str(e))
                except DataError as e:
                    exc = DataErrorRedis(str(e))
                finally:
                    if exc and generate_exc:
                        raise exc
            return wrapper
        return wrapper_func

    async def connection(self) -> Self:
        """Создание подключения к redis"""
        if not self._client:
            try:
                self._client = from_url(self.url)
                await self._client.ping()
            except (ConnectionError, ValueError) as e:
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

