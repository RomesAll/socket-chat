from uuid import UUID
from redis.asyncio import Redis
from app.business_logic.exceptions import SaveIdRefreshTokenWhiteListError
from app.infrastructure.redis.exception_handler import exception_handler


class JWTWhiteListCache:
    """
    Адаптер для реализации white list для jwt refresh токена в redis кеше.
    В redis хранятся только разрешенные токены для обновления.
    """
    def __init__(self, client: Redis):
        self.client = client
        self._prefix = 'white_list'

    @exception_handler(generate_exc=True)
    async def save_refresh_token(self, user_id: str, token_id: UUID, ex: int = 10_000) -> bool:
        """Сохранение refresh токена"""
        name = f'{self._prefix}:{user_id}:{token_id}'
        result = bool(await self.client.set(name, 'active', ex=ex))
        if not result:
            raise SaveIdRefreshTokenWhiteListError(user_id)
        return result

    @exception_handler(generate_exc=True)
    async def is_token_active(self, user_id: str, token_id: UUID) -> bool:
        """Проверка существования refresh токена"""
        result = await self.client.exists(f'{self._prefix}:{user_id}:{token_id}')
        return bool(result)

    @exception_handler(generate_exc=True)
    async def delete_refresh_token(self, user_id: str, token_id: UUID) -> bool:
        """Удаление refresh токена"""
        return bool(await self.client.delete(f'{self._prefix}:{user_id}:{token_id}'))

    @exception_handler(generate_exc=True)
    async def clear_user_token(self, user_id: str, exclude_token_ids: set[UUID] | None = None) -> int:
        """Очистка всех refresh токенов пользователя."""
        exclude_keys = set()
        if exclude_token_ids:
            exclude_keys = {f'{self._prefix}:{user_id}:{tid}' for tid in exclude_token_ids}
        pattern = f'{self._prefix}:{user_id}:*'
        deleted = 0
        async for key in self.client.scan_iter(match=pattern):
            key_str = key.decode() if isinstance(key, bytes) else key
            if key_str in exclude_keys:
                continue
            deleted += await self.client.delete(key)
        return deleted

    @exception_handler(generate_exc=True)
    async def update_refresh(self, user_id: str, old_refresh_id: UUID, new_refresh_id: UUID):
        """Метод для обновления токенов"""
        pass