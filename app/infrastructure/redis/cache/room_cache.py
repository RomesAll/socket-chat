import json
from dataclasses import asdict
from datetime import datetime
from uuid import UUID
from redis.asyncio import Redis
from app.infrastructure.redis.exception_handler import exception_handler
from app.shared.dto.enums import ChatRole
from app.shared.dto.room import RoomDTO, RoomUserMemberDTO, RoomDetailsDTO
from app.shared.log_config import LogMixin


class RoomCache(LogMixin):
    """
    Адаптер для кеша информации о комнатах.

    Хранит:\n
    - базовую информацию о комнате (RoomDTO);
    - информацию о комнате для пользователя (RoomUserMemberDTO);
    - детальную информацию о комнате (RoomDetailsDTO).
    """

    def __init__(self, client: Redis, ttl: int):
        self._client = client
        self._ttl = ttl
        self._prefix = 'room_info'

    def _key_default(self, room_id: UUID) -> str:
        return f'{self._prefix}:default_info:{room_id}'

    def _key_user_member(self, room_id: UUID) -> str:
        return f'{self._prefix}:user_member:{room_id}'

    def _key_detail(self, room_id: UUID) -> str:
        return f'{self._prefix}:detail:{room_id}'

    @exception_handler(generate_exc=False)
    async def save_default(self, room_info: RoomDTO) -> bool:
        """Сохранить базовую информацию о комнате."""
        raw_data = asdict(room_info)
        raw_data['chat_id'] = str(raw_data['chat_id'])
        raw_data['created_at'] = raw_data['created_at'].isoformat()
        raw_data['updated_at'] = raw_data['updated_at'].isoformat()

        result = await self._client.setex(
            self._key_default(room_info.chat_id),
            self._ttl,
            json.dumps(raw_data),
        )
        is_saved = bool(result)
        if not is_saved:
            self.log_warning(f'Комната {room_info.chat_id} не была сохранена в кеше (default)')
        return is_saved

    @exception_handler(generate_exc=False)
    async def get_default(self, room_id: UUID) -> RoomDTO | None:
        """Получить базовую информацию о комнате."""
        json_raw_data = await self._client.get(self._key_default(room_id))
        if not json_raw_data:
            return None
        data = json.loads(json_raw_data)
        return RoomDTO(
            chat_id=UUID(data['chat_id']),
            title=data['title'],
            description=data['description'],
            avatar_url=data['avatar_url'],
            created_at=datetime.fromisoformat(data['created_at']),
            updated_at=datetime.fromisoformat(data['updated_at']),
            max_users=data['max_users']
        )

    @exception_handler(generate_exc=False)
    async def delete_default(self, room_id: UUID) -> bool:
        """Удалить базовую информацию о комнате."""
        return bool(await self._client.delete(self._key_default(room_id)))

    @exception_handler(generate_exc=False)
    async def save_user_member(self, room_info: RoomUserMemberDTO) -> bool:
        """Сохранить информацию о комнате, в которой состоит пользователь."""
        raw_data = asdict(room_info)
        raw_data['chat_id'] = str(raw_data['chat_id'])
        raw_data['created_at'] = raw_data['created_at'].isoformat()
        raw_data['updated_at'] = raw_data['updated_at'].isoformat()
        raw_data['role'] = room_info.role.value

        result = await self._client.setex(
            self._key_user_member(room_info.chat_id),
            self._ttl,
            json.dumps(raw_data),
        )
        is_saved = bool(result)
        if not is_saved:
            self.log_warning(f'Комната {room_info.chat_id} не была сохранена в кеше (user_member)')
        return is_saved

    @exception_handler(generate_exc=False)
    async def get_user_member(self, room_id: UUID) -> RoomUserMemberDTO | None:
        """Получить информацию о комнате, в которой состоит пользователь."""
        json_raw_data = await self._client.get(self._key_user_member(room_id))
        if not json_raw_data:
            return None
        data = json.loads(json_raw_data)
        return RoomUserMemberDTO(
            chat_id=UUID(data['chat_id']),
            title=data['title'],
            description=data['description'],
            avatar_url=data['avatar_url'],
            created_at=datetime.fromisoformat(data['created_at']),
            updated_at=datetime.fromisoformat(data['updated_at']),
            user_id=data['user_id'],
            role=ChatRole(data['role']),
            members_count=data['members_count'],
        )

    @exception_handler(generate_exc=False)
    async def delete_user_member(self, room_id: UUID) -> bool:
        """Удалить информацию о комнате для пользователя."""
        return bool(await self._client.delete(self._key_user_member(room_id)))

    @exception_handler(generate_exc=False)
    async def save_detail(self, room_info: RoomDetailsDTO) -> bool:
        """Сохранить детальную информацию о комнате."""
        raw_data = asdict(room_info)
        raw_data['chat_id'] = str(raw_data['chat_id'])
        raw_data['created_at'] = raw_data['created_at'].isoformat()
        raw_data['updated_at'] = raw_data['updated_at'].isoformat()

        result = await self._client.setex(
            self._key_detail(room_info.chat_id),
            self._ttl,
            json.dumps(raw_data),
        )
        is_saved = bool(result)
        if not is_saved:
            self.log_warning(f'Комната {room_info.chat_id} не была сохранена в кеше (detail)')
        return is_saved

    @exception_handler(generate_exc=False)
    async def get_detail(self, room_id: UUID) -> RoomDetailsDTO | None:
        """Получить детальную информацию о комнате."""
        json_raw_data = await self._client.get(self._key_detail(room_id))
        if not json_raw_data:
            return None
        data = json.loads(json_raw_data)
        return RoomDetailsDTO(
            chat_id=UUID(data['chat_id']),
            title=data['title'],
            max_users=data['max_users'],
            description=data['description'],
            avatar_url=data['avatar_url'],
            owner_id=data['owner_id'],
            members_count=data['members_count'],
            admins_count=data['admins_count'],
            created_at=datetime.fromisoformat(data['created_at']),
            updated_at=datetime.fromisoformat(data['updated_at']),
        )

    @exception_handler(generate_exc=False)
    async def delete_detail(self, room_id: UUID) -> bool:
        """Удалить детальную информацию о комнате."""
        return bool(await self._client.delete(self._key_detail(room_id)))

    @exception_handler(generate_exc=False)
    async def invalidate(self, room_id: UUID) -> int:
        """
        Удалить всю информацию о комнате из кеша.

        Алгоритм:\n
        - Удалить default, user_member, detail ключи.
        - Вернуть количество удалённых.
        """
        keys = [
            self._key_default(room_id),
            self._key_user_member(room_id),
            self._key_detail(room_id),
        ]
        return await self._client.delete(*keys)