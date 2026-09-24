from uuid import UUID
from redis.asyncio import Redis
from app.business_logic.exceptions import SessionKeyNotFound, SaveSessionKeyError
from app.business_logic.redis_adapter.base import BaseRedisAdapter
from app.business_logic.redis_adapter.exception_handler import exception_handler


class SessionKeyStorage:
    """Адаптер для хранения сессионных ключей в redis кеше"""
    def __init__(self, client: Redis):
        self.client = client
        self._prefix = 'session'

    @exception_handler(generate_exc=True)
    async def save(self, user_id: str, session_id: UUID, session_key: bytes) -> bool:
        """
        Добавление session key в redis кеш
        :param user_id: id пользователя
        :param session_id: id сессии
        :param session_key: сессионный ключ
        :return: True или False
        """
        name = f'{self._prefix}:{user_id}:{session_id}'
        result = bool(
            await self.client.setex(
                name=name,
                time=3600,
                value=session_key.hex()
            )
        )
        if not result:
            raise SaveSessionKeyError(user_id, session_id)
        return result

    @exception_handler(generate_exc=True)
    async def get(self, user_id: str, session_id: UUID) -> bytes:
        """
        Получение сессионного ключа из redis кеша, если не найден, то генерируется исключение
        SessionKeyNotFound
        :param user_id: id пользователя
        :param session_id: id сессии
        :return: ключ в виде байтов
        """
        session_key_hex: bytes | str | None = await self.client.get(
            f'{self._prefix}:{user_id}:{session_id}'
        )
        if not session_key_hex:
            raise SessionKeyNotFound(user_id, session_id)
        return bytes.fromhex(session_key_hex)

    @exception_handler(generate_exc=True)
    async def delete(self, user_id: str, session_id: UUID) -> bool:
        """
        Удаление ключа из redis кеша
        :param user_id: id пользователя
        :param session_id: id сессии
        :return: True или False
        """
        return bool(
            await self.client.delete(
                f'{self._prefix}:{user_id}:{session_id}'
            )
        )
