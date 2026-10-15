import json
from dataclasses import asdict
from datetime import datetime
from redis.asyncio import Redis
from app.infrastructure.redis.exception_handler import exception_handler
from app.shared.dto.enums import RoleEnum
from app.shared.dto.user import UserDtoGet
from app.shared.log_config import LogMixin


class UserCache(LogMixin):
    """
    Адаптер для кеша информации о пользователях.
    """

    def __init__(self, client: Redis, ttl: int = 3600):
        self._client = client
        self._ttl = ttl
        self._prefix = 'user_info'

    def _key(self, user_id: str) -> str:
        return f'{self._prefix}:{user_id}'

    @exception_handler(generate_exc=False)
    async def save(self, user_info: UserDtoGet) -> bool:
        """
        Сохранить информацию о пользователе.
        """
        raw_data = asdict(user_info)
        raw_data['last_seen_at'] = raw_data['last_seen_at'].isoformat() if raw_data['last_seen_at'] else None
        raw_data['created_at'] = raw_data['created_at'].isoformat()
        raw_data['updated_at'] = raw_data['updated_at'].isoformat()

        result = await self._client.setex(
            self._key(user_info.id),
            self._ttl,
            json.dumps(raw_data),
        )
        is_saved = bool(result)
        if not is_saved:
            self.log_warning(f'Пользователь {user_info.id} не был сохранен в кеше')
        return is_saved

    @exception_handler(generate_exc=False)
    async def get(self, user_id: str) -> UserDtoGet | None:
        """
        Получить информацию о пользователе из кеша.
        """
        json_raw_data = await self._client.get(self._key(user_id))
        if not json_raw_data:
            return None
        user_info = json.loads(json_raw_data)
        return UserDtoGet(
            id=user_info['id'],
            display_name=user_info['display_name'],
            avatar_url=user_info['avatar_url'],
            created_at=datetime.fromisoformat(user_info['created_at']),
            updated_at=datetime.fromisoformat(user_info['updated_at']),
            description=user_info['description'],
            years_old=user_info['years_old'],
            role=RoleEnum(user_info['role']),
            email=user_info['email'],
            last_seen_at=(
                datetime.fromisoformat(user_info['last_seen_at'])
                if user_info['last_seen_at'] else None
            ),
        )

    @exception_handler(generate_exc=False)
    async def delete(self, user_id: str) -> bool:
        """
        Удалить информацию о пользователе из кеша.
        """
        return bool(await self._client.delete(self._key(user_id)))