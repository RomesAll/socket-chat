import datetime
import json
from uuid import UUID
from redis.asyncio import Redis
from app.business_logic.redis_adapter.exception_handler import exception_handler
from app.shared.dto.message import MessageDtoGet
from app.shared.dto.user import UserDtoGet


class Cache:
    """
    Адаптер для redis кеша. Сохраняет следующую информацию:\n
    1) общая информация о пользователе;
    2) кеш сообщений в чате;
    3) в сети ли текущий пользователь или нет;
    4) счетчик непрочитанных сообщений пользователя.
    """
    def __init__(self, client: Redis):
        self.client = client
        self._base_prefix = 'cache'
        self._user_info_prefix = 'user_info'
        self._chat_msg = 'chat_msg'
        self._user_is_online = 'user_is_online'
        self._user_count_msg_unread = 'user_count_msg_unread'

    @exception_handler(generate_exc=False)
    async def save_user_info(self, user_info: UserDtoGet, ttl_seconds: int = 3600) -> bool:
        """Сохранение информации о пользователе в кеш"""
        key = f'{self._user_info_prefix}:{user_info.id}'
        save_user_info = user_info.model_dump(mode='json', exclude_none=True, exclude_unset=True)
        result = await self.client.hset(key, mapping=save_user_info)
        await self.client.expire(key, ttl_seconds)
        return bool(result)

    @exception_handler(generate_exc=False)
    async def delete_user_info(self, user_id: str):
        """Удаление информации о пользователе в кеш"""
        key = f'{self._user_info_prefix}:{str(user_id)}'
        await self.client.delete(key)

    @exception_handler(generate_exc=False)
    async def get_user_info(self, user_id: str) -> dict | None:
        """Получение информации о пользователе из кеша"""
        key = f'{self._user_info_prefix}:{user_id}'
        result = await self.client.hgetall(key)
        if not result:
            return None
        return result

    @exception_handler(generate_exc=False)
    async def save_chat_msg_info(self, msg_info: MessageDtoGet, ttl_seconds: int = 3600 * 24) -> int:
        """Сохранение информации о сообщении в кеш"""
        date = msg_info.created_at.date().isoformat()
        key = f'{self._chat_msg}:{msg_info.chat_id}:history:{date}'
        save_msg_info = msg_info.model_dump(mode='json')
        result = await self.client.rpush(key, json.dumps(save_msg_info))
        await self.client.expire(key, ttl_seconds, nx=True)
        return result

    @exception_handler(generate_exc=False)
    async def get_chat_msg_info(self, chat_id: UUID, msg_date: datetime.date) -> list[dict]:
        """Получение информации о сообщении из кеша"""
        key = f'{self._chat_msg}:{chat_id}:history:{msg_date.isoformat()}'
        results = await self.client.lrange(key, 0, -1)
        return [json.loads(res) for res in results]

    @exception_handler(generate_exc=False)
    async def user_is_online(self, user_id: str) -> bool:
        """В сети ли пользователь"""
        key = f'{self._user_is_online}:{user_id}:online'
        result = await self.client.get(key)
        if not result:
            return False
        return bool(result)

    @exception_handler(generate_exc=False)
    async def set_user_online(self, user_id: str) -> bool:
        """Установить online у пользователя"""
        key = f'{self._user_is_online}:{user_id}:online'
        result = await self.client.set(key, True)
        return bool(result)

    @exception_handler(generate_exc=False)
    async def incr_unread_msg(self, chat_id: UUID, user_id: str) -> int:
        """Увеличение счетчика непрочитанных сообщений"""
        key = f'{self._user_count_msg_unread}:{user_id}:unread'
        result = await self.client.hincrby(key, str(chat_id))
        return result

    @exception_handler(generate_exc=False)
    async def set_zero_unread_msg(self, chat_id: UUID, user_id: str) -> int:
        """Обнуление счетчика непрочитанных сообщений"""
        key = f'{self._user_count_msg_unread}:{user_id}:unread'
        result = await self.client.hset(key, str(chat_id), '0')
        return result

    @exception_handler(generate_exc=False)
    async def get_unread_msg(self, user_id: str) -> dict:
        """Получение счетчиков непрочитанных сообщений для главного экрана"""
        key = f'{self._user_count_msg_unread}:{user_id}:unread'
        all_unread = await self.client.hgetall(key)
        return all_unread