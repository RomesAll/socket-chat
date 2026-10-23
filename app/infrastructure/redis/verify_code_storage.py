from redis.asyncio import Redis
from app.business_logic.exceptions import SaveCodeError
from app.infrastructure.redis.exception_handler import exception_handler


class VerifyCodeStorage:
    """Адаптер для хранения кодов подтверждения (при логине и регистрации) redis кеше"""
    def __init__(self, client: Redis, ttl: int):
        self.client = client
        self._prefix = 'verify_code'
        self._ttl = ttl

    @exception_handler(generate_exc=True)
    async def save(self, user_id: str, code: int):
        """
        Сохранение кода подтверждения для auth и регистрации.
        user_id - идентификатор пользователя
        code - числовой код подтверждения
        ttl - время жизни кода
        """
        name = f'{self._prefix}:{user_id}'
        result = bool(await self.client.setex(
            name=name,
            time=self._ttl,
            value=code
        ))
        if not result:
            raise SaveCodeError(user_id)

    @exception_handler(generate_exc=True)
    async def validate_code(self, user_id: str, code: int) -> bool:
        """
        Проверка корректности введенного кода подтверждения
        user_id - идентификатор пользователя
        code - числовой код подтверждения
        """
        name = f'{self._prefix}:{user_id}'
        result = await self.client.get(name)
        if type(result) == bytes:
            if result.decode() == str(code):
                return True
        return False