from uuid import UUID
from app.business_logic.redis_adapter import Cache
from app.business_logic.unit_of_work import UnitOfWork
from app.business_logic.websocket.broker import WSBroker
from app.data_layer.models.events import EventType
from app.shared.dto.chat import ChatDtoGet, ChatMemberDtoGet, ChatMemberDtoSave, ChatMemberDtoUpdate
from app.shared.dto.dto_relation_ship import ChatDtoGetWithRelation
from app.shared.dto.room import RoomDtoGet
from app.shared.log_config import LogMixin
from app.shared.config import get_config, AppMode, BaseConfig


def _get_config() -> BaseConfig:
    return get_config()


class ChatService(LogMixin):
    """Сервис для управления комнатами"""
    def __init__(self, uow: UnitOfWork, cache: Cache, broker: WSBroker):
        self._uow = uow
        self._cache = cache
        self._broker = broker

    async def get_chat_by_id(self, chat_id: UUID) -> ChatDtoGet:
        """Получить чат по id"""
        async with self._uow as uow:
            chat_orm = await uow.chat_repo.get_chat_by_id(chat_id)
            response = ChatDtoGet(**chat_orm.to_dict())
            return response

    async def get_chat_by_id_with_relation(self, chat_id: UUID) -> ChatDtoGetWithRelation:
        """Получить чат по id с relationship"""
        async with self._uow as uow:
            chat_orm = await uow.chat_repo.get_chat_by_id(chat_id=chat_id, with_relation=True)
            response = ChatDtoGetWithRelation(
                **chat_orm.to_dict(),
                room=RoomDtoGet(**chat_orm.room.to_dict()),
                members=[ChatMemberDtoGet(**member.to_dict()) for member in chat_orm.members]
            )
            return response

    async def get_user_chats(self, user_id: str) -> list[ChatMemberDtoGet]:
        """Получить все чаты пользователя"""
        async with self._uow as uow:
            chat_members_orm = await uow.chat_repo.get_user_chats(user_id)
            response = [
                ChatMemberDtoGet(**chat_member.to_dict())
                for chat_member in chat_members_orm
            ]
            return response

    async def get_chat_by_room(self, room_id: UUID) -> list[ChatDtoGetWithRelation]:
        """Получить все чаты в комнате"""
        async with self._uow as uow:
            chats_orm = await uow.chat_repo.get_chat_by_room(room_id, with_relation=True)
            response = [
                ChatDtoGetWithRelation(
                    **chat.to_dict(),
                    room=RoomDtoGet(**chat.room.to_dict()),
                    members=[ChatMemberDtoGet(**member.to_dict()) for member in chat.members]
                )
                for chat in chats_orm
            ]
            return response

    async def get_chat_members(self, chat_id: UUID) -> list[ChatMemberDtoGet]:
        """Получить участников чата"""
        async with self._uow as uow:
            chats_orm = await uow.chat_repo.get_chat_members(chat_id)
            response = [
                ChatMemberDtoGet(**chat.to_dict())
                for chat in chats_orm
            ]
            return response

    async def add_chat_member(self, chat_member: ChatMemberDtoSave) -> ChatMemberDtoGet:
        """Добавить участника в комнату"""
        async with self._uow as uow:
            chat_orm = await uow.chat_repo.add_chat_member(chat_member)
            self.log_info(f'Пользователь {chat_member.user_id} был добавлен в чат {chat_member.chat_id}')
            response = ChatMemberDtoGet(**chat_orm.to_dict())
            if _get_config().mode not in (AppMode.DEV,):
                uow.add_event(
                    event_name='Add member in chat',
                    payload=response.model_dump(),
                    event_type=EventType.ADD_MEMBER_IN_CHAT
                )
                self.log_info(f'Событие {EventType.NEW_ROOM} зарегистрировано')
        await self._broker.publish_join_chat(
            action_type='JOIN_CHAT',
            chat_id=response.chat_id,
            user_id=chat_member.user_id
        )
        return response

    async def remove_chat_member(self, chat_id: UUID, user_id: str) -> int:
        """Удалить участника из комнаты"""
        async with self._uow as uow:
            res = await uow.chat_repo.remove_chat_member(chat_id, user_id)
            self.log_info(f'Пользователь {user_id} был удален из чата {chat_id}')
            if _get_config().mode not in (AppMode.DEV,):
                uow.add_event(
                    event_name='Remove member in chat',
                    payload={'user_id': user_id},
                    event_type=EventType.REMOVE_MEMBER_IN_CHAT
                )
                self.log_info(f'Событие {EventType.NEW_ROOM} зарегистрировано')
        await self._broker.publish_leave_chat(
            action_type='LEAVE_CHAT',
            chat_id=chat_id,
            user_id=user_id
        )
        return res

    async def update_member(
            self, chat_id: UUID, user_id: str, update_member: ChatMemberDtoUpdate
    ) -> ChatMemberDtoGet:
        """Обновить участника комнаты"""
        async with self._uow as uow:
            chat_member_orm = await uow.chat_repo.update_member(chat_id, user_id, update_member)
            response = ChatMemberDtoGet(**chat_member_orm.to_dict())
            return response