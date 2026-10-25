import json
from dataclasses import asdict
from datetime import date, datetime
from uuid import UUID
from redis.asyncio import Redis
from app.infrastructure.redis.exception_handler import exception_handler
from app.shared.dto.enums import MessageType
from app.shared.dto.message import MessageEncryptedReadDTO
from app.shared.log_config import LogMixin


class ChatMessageCache(LogMixin):
    """
    Адаптер для кеша истории сообщений чата.
    """

    def __init__(self, client: Redis, ttl: int):
        self._client = client
        self._ttl = ttl
        self._prefix = 'chat_msg'

    def _key(self, chat_id: UUID, msg_date: date) -> str:
        return f'{self._prefix}:{chat_id}:history:{msg_date.isoformat()}'

    @exception_handler(generate_exc=False)
    async def push(self, msg_info: MessageEncryptedReadDTO) -> int | None:
        """
        Добавить сообщение в историю чата.

        Алгоритм:\n
        - Если нет body_encrypted — не кешируем, вернуть None.
        - Сформировать ключ по chat_id и дате сообщения.
        - Сериализовать DTO в JSON.
        - RPUSH в список.
        - Установить TTL (только если его ещё нет).
        """
        if not msg_info.body_encrypted:
            return None

        msg_date = msg_info.created_at.date()
        raw_data = asdict(msg_info)
        raw_data['id'] = str(raw_data['id'])
        raw_data['chat_id'] = str(raw_data['chat_id'])
        raw_data['reply_to_message_id'] = (
            str(raw_data['reply_to_message_id']) if raw_data['reply_to_message_id'] else None
        )
        raw_data['forwarded_from_message_id'] = (
            str(raw_data['forwarded_from_message_id']) if raw_data['forwarded_from_message_id'] else None
        )
        raw_data['type'] = msg_info.type.value
        raw_data['created_at'] = raw_data['created_at'].isoformat()
        raw_data['updated_at'] = raw_data['updated_at'].isoformat()
        raw_data['body_encrypted'] = raw_data['body_encrypted'].decode()
        key = self._key(msg_info.chat_id, msg_date)
        result = await self._client.rpush(key, json.dumps(raw_data))
        await self._client.expire(key, self._ttl)
        return result

    @exception_handler(generate_exc=False)
    async def get_history(self, chat_id: UUID, msg_date: date) -> list[MessageEncryptedReadDTO]:
        """
        Получить историю сообщений чата за дату.

        Алгоритм:\n
        - Сформировать ключ.
        - LRANGE весь список.
        - Десериализовать каждое сообщение в DTO.
        """
        raw_data = await self._client.lrange(self._key(chat_id, msg_date), 0, -1)
        results = []
        for msg in raw_data:
            current = json.loads(msg)
            results.append(MessageEncryptedReadDTO(
                id=UUID(current['id']),
                chat_id=UUID(current['chat_id']),
                sender_id=current['sender_id'],
                type=MessageType(current['type']),
                reply_to_message_id=(
                    UUID(current['reply_to_message_id'])
                    if current.get('reply_to_message_id') else None
                ),
                forwarded_from_message_id=(
                    UUID(current['forwarded_from_message_id'])
                    if current.get('forwarded_from_message_id') else None
                ),
                forwarded_from_user_id=current.get('forwarded_from_user_id'),
                body_encrypted=current['body_encrypted'].encode(),
                is_edited=current['is_edited'],
                created_at=datetime.fromisoformat(current['created_at']),
                updated_at=datetime.fromisoformat(current['updated_at']),
            ))
        return results

    @exception_handler(generate_exc=False)
    async def delete_history(self, chat_id: UUID, msg_date: date) -> bool:
        """Удалить историю сообщений чата за дату."""
        return bool(await self._client.delete(self._key(chat_id, msg_date)))