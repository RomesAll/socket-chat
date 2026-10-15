from redis.asyncio import Redis
from app.infrastructure.redis.exception_handler import exception_handler
from app.shared.log_config import LogMixin


class PresenceCache(LogMixin):
    """
    Адаптер для кеша online-статуса пользователей.
    """

    def __init__(self, client: Redis, ttl: int = 300):
        self._client = client
        self._ttl = ttl
        self._prefix = 'user_is_online'

    def _key(self, user_id: str) -> str:
        return f'{self._prefix}:{user_id}:online'

    @exception_handler(generate_exc=False)
    async def set_online(self, user_id: str) -> bool:
        """
        Установить пользователя онлайн.
        """
        result = await self._client.set(self._key(user_id), '1', ex=self._ttl)
        return bool(result)

    @exception_handler(generate_exc=False)
    async def is_online(self, user_id: str) -> bool:
        """Проверить, в сети ли пользователь."""
        result = await self._client.get(self._key(user_id))
        return bool(result)

    @exception_handler(generate_exc=False)
    async def set_offline(self, user_id: str) -> bool:
        """Установить пользователя офлайн."""
        return bool(await self._client.delete(self._key(user_id)))