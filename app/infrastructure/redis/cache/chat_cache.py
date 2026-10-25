import json
from dataclasses import asdict
from datetime import datetime
from uuid import UUID
from redis.asyncio import Redis
from app.shared.dto.chat import ChatDTO
from app.shared.dto.enums import ChatType
from app.shared.log_config import LogMixin


class ChatCache(LogMixin):
    """
    Адаптер для кеша информации о чатах и пользователей чатов.
    """

    def __init__(self, client: Redis, ttl: int):
        self._client = client
        self._ttl = ttl
        self._prefix = 'chat'

    def _key_chat(self, chat_id: UUID) -> str:
        return f'{self._prefix}:{chat_id}:info'

    async def get(self, chat_id: UUID) -> ChatDTO | None:
        """Получить информацию о чате из кеша."""
        key = self._key_chat(chat_id)
        json_raw_data = await self._client.get(key)
        if not json_raw_data:
            return None
        data = json.loads(json_raw_data)
        last_message_at = data.get('last_message_at')
        last_message_id = data.get('last_message_id')
        if last_message_at:
            last_message_at = datetime.fromisoformat(last_message_at)
        if last_message_id:
            last_message_id = UUID(last_message_id)
        return ChatDTO(
            id=UUID(data['id']),
            type=ChatType(data['type']),
            is_active=data['is_active'],
            last_message_at=last_message_at,
            last_message_id=last_message_id,
            created_at=data['created_at'],
            updated_at=data['updated_at']
        )

    async def save(self, chat_dto: ChatDTO) -> bool:
        """Сохранить информацию о чате в кеш."""
        key = self._key_chat(chat_dto.id)
        raw_data = asdict(chat_dto)
        raw_data['id'] = str(raw_data['id'])
        raw_data['type'] = str(raw_data['type'].value)
        raw_data['created_at'] = raw_data['created_at'].isoformat()
        raw_data['updated_at'] = raw_data['updated_at'].isoformat()
        if chat_dto.last_message_at:
            raw_data['last_message_at'] = raw_data['last_message_at'].isoformat()
        if chat_dto.last_message_id:
            raw_data['last_message_id'] = str(raw_data['last_message_id'])

        result = await self._client.setex(
            key,
            self._ttl,
            json.dumps(raw_data),
        )
        is_saved = bool(result)
        if not is_saved:
            self.log_warning(f'Чат {chat_dto.id} не была сохранен в кеше')
        return is_saved

    async def delete(self, chat_id: UUID) -> bool:
        return bool(await self._client.delete(self._key_chat(chat_id)))