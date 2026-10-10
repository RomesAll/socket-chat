from datetime import datetime, date
import json
from uuid import UUID
from redis.asyncio import Redis
from app.business_logic.redis_adapter.exception_handler import exception_handler
from app.shared.dto.enums import RoleEnum, ChatRole, MessageType
from app.shared.dto.message import MessageEncryptedReadDTO
from app.shared.dto.room import RoomDTO, RoomUserMemberDTO, RoomDetailsDTO
from dataclasses import asdict
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
        self._room_info = 'room_info'

    @exception_handler(generate_exc=False)
    async def save_room_default_info(self, room_info: RoomDTO, ttl_seconds: int = 3600) -> bool:
        """Сохранение информации о комнате в кеш"""
        key = f'{self._room_info}:default_info:{room_info.chat_id}'
        raw_data = asdict(room_info)
        raw_data['chat_id'] = str(raw_data['chat_id'])
        raw_data['created_at'] = raw_data['created_at'].isoformat()
        raw_data['updated_at'] = raw_data['updated_at'].isoformat()
        result = await self.client.setex(key, ttl_seconds, json.dumps(raw_data))
        return bool(result)

    @exception_handler(generate_exc=False)
    async def save_room_user_member_info(self, room_info: RoomUserMemberDTO, ttl_seconds: int = 3600) -> bool:
        """Сохранение информации о комнате, в которых состоит выбранный пользователь в кеш"""
        key = f'{self._room_info}:user_member:{room_info.chat_id}'
        raw_data = asdict(room_info)
        raw_data['chat_id'] = str(raw_data['chat_id'])
        raw_data['created_at'] = raw_data['created_at'].isoformat()
        raw_data['updated_at'] = raw_data['updated_at'].isoformat()
        result = await self.client.setex(key, ttl_seconds, json.dumps(raw_data))
        return bool(result)

    @exception_handler(generate_exc=False)
    async def save_room_detail_info(self, room_info: RoomDetailsDTO, ttl_seconds: int = 3600) -> bool:
        """Сохранение детальной информации о комнате в кеш."""
        key = f'{self._room_info}:detail:{room_info.chat_id}'
        raw_data = asdict(room_info)
        raw_data['chat_id'] = str(raw_data['chat_id'])
        raw_data['created_at'] = raw_data['created_at'].isoformat()
        raw_data['updated_at'] = raw_data['updated_at'].isoformat()
        result = await self.client.setex(key, ttl_seconds, json.dumps(raw_data))
        return bool(result)

    @exception_handler(generate_exc=False)
    async def get_room_default_info(self, room_id: UUID) -> RoomDTO | None:
        """Получение информации о комнате из кеша."""
        key = f'{self._room_info}:default_info:{room_id}'
        json_raw_data = await self.client.get(key)
        if not json_raw_data:
            return None
        room_info = json.loads(json_raw_data)
        return RoomDTO(
            chat_id=UUID(room_info['chat_id']),
            title=room_info['title'],
            description=room_info['description'],
            avatar_url=room_info['avatar_url'],
            created_at=datetime.fromisoformat(room_info['created_at']),
            updated_at=datetime.fromisoformat(room_info['updated_at']),
        )

    @exception_handler(generate_exc=False)
    async def get_room_user_member_info(self, room_id: UUID) -> RoomUserMemberDTO | None:
        """Получение информации о комнате из кеша."""
        key = f'{self._room_info}:user_member:{room_id}'
        json_raw_data = await self.client.get(key)
        if not json_raw_data:
            return None
        room_info = json.loads(json_raw_data)
        return RoomUserMemberDTO(
            chat_id=UUID(room_info['chat_id']),
            title=room_info['title'],
            description=room_info['description'],
            avatar_url=room_info['avatar_url'],
            created_at=datetime.fromisoformat(room_info['created_at']),
            updated_at=datetime.fromisoformat(room_info['updated_at']),
            user_id=room_info['user_id'],
            role=ChatRole(room_info['role']),
            members_count=room_info['members_count']
        )

    @exception_handler(generate_exc=False)
    async def get_room_detail_info(self, room_id: UUID) -> RoomDetailsDTO | None:
        """Получение информации о комнате из кеша."""
        key = f'{self._room_info}:detail:{room_id}'
        json_raw_data = await self.client.get(key)
        if not json_raw_data:
            return None
        room_info = json.loads(json_raw_data)
        return RoomDetailsDTO(
            chat_id=UUID(room_info['chat_id']),
            title=room_info['title'],
            description=room_info['description'],
            avatar_url=room_info['avatar_url'],
            created_at=datetime.fromisoformat(room_info['created_at']),
            updated_at=datetime.fromisoformat(room_info['updated_at']),
            members_count=room_info['members_count'],
            max_users=room_info['max_users'],
            owner_id=room_info['owner_id'],
            admins_count=room_info['admins_count']
        )

    @exception_handler(generate_exc=False)
    async def save_user_info(self, user_info: UserDtoGet, ttl_seconds: int = 3600) -> bool:
        """Сохранение информации о пользователе в кеш."""
        key = f'{self._user_info_prefix}:{user_info.id}'
        raw_data = asdict(user_info)
        raw_data['last_seen_at'] = raw_data['last_seen_at'].isoformat()
        raw_data['created_at'] = raw_data['created_at'].isoformat()
        raw_data['updated_at'] = raw_data['updated_at'].isoformat()
        result = await self.client.setex(key, ttl_seconds, json.dumps(raw_data))
        return bool(result)

    @exception_handler(generate_exc=False)
    async def delete_user_info(self, user_id: str):
        """Удаление информации о пользователе из кеша."""
        key = f'{self._user_info_prefix}:{str(user_id)}'
        await self.client.delete(key)

    @exception_handler(generate_exc=False)
    async def get_user_info(self, user_id: str) -> UserDtoGet | None:
        """Получение информации о пользователе из кеша"""
        key = f'{self._user_info_prefix}:{user_id}'
        json_raw_data = await self.client.get(key)
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
            last_seen_at=datetime.fromisoformat(user_info['last_seen_at']),
        )

    @exception_handler(generate_exc=False)
    async def save_chat_msg_info(self, msg_info: MessageEncryptedReadDTO, ttl_seconds: int = 3600 * 24) -> int | None:
        """Сохранение информации о сообщении в кеш"""
        if not msg_info.body_encrypted:
            return None
        date_msg = msg_info.created_at.date().isoformat()
        key = f'{self._chat_msg}:{msg_info.chat_id}:history:{date_msg}'
        raw_data = asdict(msg_info)

        raw_data['id'] = str(raw_data['id'])
        raw_data['chat_id'] = str(raw_data['chat_id'])
        raw_data['reply_to_message_id'] = str(raw_data['reply_to_message_id'])
        raw_data['forwarded_from_message_id'] = str(raw_data['forwarded_from_message_id'])
        raw_data['forwarded_from_user_id'] = str(raw_data['forwarded_from_user_id'])
        raw_data['created_at'] = raw_data['created_at'].isoformat()
        raw_data['updated_at'] = raw_data['updated_at'].isoformat()

        result = await self.client.rpush(key, json.dumps(raw_data))
        await self.client.expire(key, ttl_seconds, nx=True)
        return result

    @exception_handler(generate_exc=False)
    async def get_chat_msg_info(self, chat_id: UUID, msg_date: date) -> list[MessageEncryptedReadDTO]:
        """Получение информации о сообщении из кеша"""
        key = f'{self._chat_msg}:{chat_id}:history:{msg_date.isoformat()}'
        raw_data = await self.client.lrange(key, 0, -1)
        results = []
        for msg in raw_data:
            current_msg = json.loads(msg)
            reply_to_message_id = None
            forwarded_from_message_id = None
            if rep_msg := current_msg.get('reply_to_message_id'):
                reply_to_message_id = UUID(rep_msg)
            if for_msg_id := current_msg.get('forwarded_from_message_id'):
                forwarded_from_message_id = UUID(for_msg_id)
            results.append(
                MessageEncryptedReadDTO(
                    id=UUID(current_msg['id']),
                    chat_id=UUID(current_msg['chat_id']),
                    sender_id=current_msg['sender_id'],
                    type=MessageType(current_msg['type']),
                    reply_to_message_id=reply_to_message_id,
                    forwarded_from_user_id=current_msg['forwarded_from_user_id'],
                    forwarded_from_message_id=forwarded_from_message_id,
                    body_encrypted=current_msg['body_encrypted'],
                    is_edited=current_msg['is_edited'],
                    created_at=datetime.fromisoformat(current_msg['created_at']),
                    updated_at=datetime.fromisoformat(current_msg['updated_at']),
                )
            )
        return results

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