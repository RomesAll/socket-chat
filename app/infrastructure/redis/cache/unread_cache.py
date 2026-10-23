from uuid import UUID
from redis.asyncio import Redis
from app.infrastructure.redis.exception_handler import exception_handler
from app.shared.log_config import LogMixin


class UnreadCache(LogMixin):
    """
    Адаптер для кеша счётчиков непрочитанных сообщений.
    """

    def __init__(self, client: Redis):
        self._client = client
        self._prefix = 'user_count_msg_unread'

    def _key(self, user_id: str) -> str:
        return f'{self._prefix}:{user_id}:unread'

    @exception_handler(generate_exc=False)
    async def incr(self, chat_id: UUID, user_id: str) -> int:
        """
        Увеличить счётчик непрочитанных для чата.
        """
        result = await self._client.hincrby(self._key(user_id), str(chat_id))
        return result

    @exception_handler(generate_exc=False)
    async def reset(self, chat_id: UUID, user_id: str) -> int:
        """
        Обнулить счётчик непрочитанных для чата.
        """
        return await self._client.hset(self._key(user_id), str(chat_id), '0')

    @exception_handler(generate_exc=False)
    async def get_all(self, user_id: str) -> dict[str, int]:
        """
        Получить все счётчики непрочитанных пользователя.
        """
        raw = await self._client.hgetall(self._key(user_id))
        return {k.decode() if isinstance(k, bytes) else k: int(v) for k, v in raw.items()}

    @exception_handler(generate_exc=False)
    async def delete(self, user_id: str) -> bool:
        """Удалить все счётчики пользователя."""
        return bool(await self._client.delete(self._key(user_id)))