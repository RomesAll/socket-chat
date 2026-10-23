from redis.asyncio import Redis
from app.infrastructure.redis.exception_handler import exception_handler
from app.shared.log_config import LogMixin


class PresenceCache(LogMixin):
    """
    Адаптер для кеша online-статуса пользователей.
    """

    def __init__(self, client: Redis, ttl: int):
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
        count = await self._client.incrby(self._key(user_id), 1)
        await self._client.expire(self._key(user_id), self._ttl)
        return count > 0

    @exception_handler(generate_exc=False)
    async def is_online(self, user_id: str) -> bool:
        """Проверить, в сети ли пользователь."""
        count = await self._client.get(self._key(user_id))
        if not count:
            return False
        return int(count) > 0

    @exception_handler(generate_exc=False)
    async def set_offline(self, user_id: str) -> bool:
        """Установить пользователя офлайн."""
        key = self._key(user_id)
        count = await self._client.decr(key)
        if count <= 0:
            await self._client.delete(key)
            return False
        await self._client.expire(key, self._ttl)
        return True