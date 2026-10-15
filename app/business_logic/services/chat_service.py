from uuid import UUID
from app.business_logic.mappers.chat_mapper import ChatMapper
from app.business_logic.unit_of_work import UnitOfWork
from app.domain.events import ChatMemberAdded, ChatMemberRoleChanged, ChatMemberRemoved, ChatOwnershipTransferred
from app.infrastructure.redis import ChatCache
from app.shared.dto.chat import ChatSaveDTO, ChatDTO, ChatUpdateDTO, ChatMemberDTO, ChatMemberSaveDTO, \
    ChatMemberUpdateDTO
from app.shared.dto.enums import ChatRole
from app.shared.log_config import LogMixin


class ChatService(LogMixin):
    """Сервис для управления комнатами"""

    def __init__(self, uow: UnitOfWork, mapper: ChatMapper, cache: ChatCache):
        self._uow = uow
        self._mapper = mapper
        self._cache = cache

    async def get(self, chat_id: UUID) -> ChatDTO:
        """
        Получить информацию о чате по ID.
        :exception RecordNotFound если не найдена запись.
        """
        cached = await self._cache.get(chat_id)
        if cached:
            return cached
        chat_orm = await self._uow.chat_repo.get_record_by_id(chat_id)
        chat_dto = self._mapper.chat_to_dto(chat_orm)
        self._uow.add_after_commit(lambda: self._cache.save(chat_dto))
        return chat_dto

    async def get_many(self, limit: int, offset: int) -> list[ChatDTO]:
        """Получить информацию о чатах с использованием пагинации."""
        chat_many_orm = await self._uow.chat_repo.get_records(limit, offset)
        result_dtos = [
            self._mapper.chat_to_dto(chat)
            for chat in chat_many_orm
        ]
        return result_dtos

    async def find(self, chat_id: UUID) -> ChatDTO | None:
        """Поиск информацию о чате. Вернет None, если не найдена запись."""
        return await self._uow.chat_read_repo.find_by_id(chat_id)

    async def get_chats_user(self, user_id: str) -> list[ChatDTO]:
        """Получить информацию о чатах пользователя. Вернет пустой list, если чатов нет."""
        return await self._uow.chat_read_repo.get_user_chats(user_id)

    async def user_is_member(self, user_id: str, chat_id: UUID) -> bool:
        """Является ли пользователь участником чата."""
        return await self._uow.chat_read_repo.is_member(chat_id, user_id)

    async def save(self, chat_dto: ChatSaveDTO) -> ChatDTO:
        """Сохранить информацию о чате."""
        chat_orm = await self._uow.chat_repo.save(chat_dto)
        saved_chat = self._mapper.chat_to_dto(chat_orm)
        self.log_info(f"Создан чат {saved_chat.id}")
        return saved_chat

    async def update(self, chat_id: UUID, chat_dto: ChatUpdateDTO) -> ChatDTO:
        """Обновить информацию о чате."""
        chat_orm = await self._uow.chat_repo.update(chat_id, chat_dto)
        updated_chat = self._mapper.chat_to_dto(chat_orm)
        self.log_info(f"Обновлен чат {updated_chat.id}")
        return updated_chat

    async def delete(self, chat_id: UUID) -> ChatDTO:
        """Удалить информацию о пользователе."""
        chat_orm = await self._uow.chat_repo.delete(chat_id)
        deleted_chat = self._mapper.chat_to_dto(chat_orm)
        self.log_info(f"Удалён чат {deleted_chat.id}")
        return deleted_chat

    async def is_member(self, chat_id: UUID, user_id: str) -> bool:
        """Является ли пользователь участником чата."""
        return await self._uow.chat_member_read_repo.is_member(chat_id, user_id)

    async def is_admin(self, chat_id: UUID, user_id: str) -> bool:
        """Является ли пользователь owner или admin чата."""
        return await self._uow.chat_member_read_repo.is_admin(chat_id, user_id)

    async def get_member(self, chat_id: UUID, user_id: str) -> ChatMemberDTO:
        """
        Получить участника чата.
        :exception RecordNotFound если не найдена запись.
        """
        member_orm = await self._uow.chat_member_repo.get_by_ids(chat_id, user_id)
        return self._mapper.member_to_dto(member_orm)

    async def find_member(self, chat_id: UUID, user_id: str) -> ChatMemberDTO | None:
        """Найти участника чата. Вернет None, если не найден."""
        return await self._uow.chat_member_read_repo.get_by_ids(chat_id, user_id)

    async def get_members(self, chat_id: UUID) -> list[ChatMemberDTO]:
        """Получить участников чата."""
        return await self._uow.chat_member_read_repo.list_by_chat(chat_id)

    async def add_member(self, member_dto: ChatMemberSaveDTO) -> ChatMemberDTO:
        """Добавить участника в чат."""
        member_orm = await self._uow.chat_member_repo.save(member_dto)
        added_member = self._mapper.member_to_dto(member_orm)
        self._uow.add_event(ChatMemberAdded(
            chat_id=added_member.chat_id,
            user_id=added_member.user_id,
            role=added_member.role
        ))
        self.log_info(
            f"В чат {member_dto.chat_id} добавлен участник {member_dto.user_id} "
            f"с ролью {member_dto.role}"
        )
        return added_member

    async def update_member(
        self, chat_id: UUID, user_id: str, member_dto: ChatMemberUpdateDTO,
    ) -> ChatMemberDTO:
        """Обновить информацию об участнике чата."""
        member_orm = await self._uow.chat_member_repo.update(
            (chat_id, user_id), member_dto,
        )
        updated_member = self._mapper.member_to_dto(member_orm)
        self.log_info(f"Обновлён участник {user_id} в чате {chat_id}")
        return updated_member

    async def set_role(
        self, chat_id: UUID, user_id: str, role: ChatRole,
    ) -> ChatMemberDTO:
        """Поменять роль участника чата."""
        old_member_orm = await self._uow.chat_member_repo.get_by_ids(chat_id, user_id)
        member_orm = await self._uow.chat_member_repo.set_role(chat_id, user_id, role)
        updated_member = self._mapper.member_to_dto(member_orm)
        self._uow.add_event(ChatMemberRoleChanged(
            chat_id=updated_member.chat_id,
            user_id=updated_member.user_id,
            old_role=old_member_orm.role,
            new_role=member_orm.role
        ))
        self.log_info(f"Участнику {user_id} в чате {chat_id} установлена роль {role}")
        return updated_member

    async def set_mute(
        self, chat_id: UUID, user_id: str, mute: bool,
    ) -> ChatMemberDTO:
        """Включить или выключить mute участника."""
        member_orm = await self._uow.chat_member_repo.set_mute(chat_id, user_id, mute)
        updated_member = self._mapper.member_to_dto(member_orm)
        self.log_info(f"Участник {user_id} в чате {chat_id}: mute={mute}")
        return updated_member

    async def set_last_read(
        self, chat_id: UUID, user_id: str, message_id: UUID | None,
    ) -> ChatMemberDTO:
        """Обновить last_read_message_id участника."""
        member_orm = await self._uow.chat_member_repo.set_last_read(
            chat_id, user_id, message_id,
        )
        return self._mapper.member_to_dto(member_orm)

    async def remove_member(self, chat_id: UUID, user_id: str) -> ChatMemberDTO:
        """Удалить участника из чата."""
        member_orm = await self._uow.chat_member_repo.remove(chat_id, user_id)
        removed_member = self._mapper.member_to_dto(member_orm)
        self._uow.add_event(ChatMemberRemoved(
            chat_id=removed_member.chat_id,
            user_id=removed_member.user_id,
        ))
        self.log_info(f"Из чата {chat_id} удалён участник {user_id}")
        return removed_member

    async def transfer_ownership(
        self, chat_id: UUID, from_user: str, to_user: str,
    ) -> None:
        """Передать владение чатом от одного участника другому."""
        await self._uow.chat_member_repo.set_role(chat_id, to_user, ChatRole.OWNER)
        await self._uow.chat_member_repo.set_role(chat_id, from_user, ChatRole.ADMIN)
        self._uow.add_event(ChatOwnershipTransferred(
            chat_id=chat_id,
            from_user=from_user,
            to_user=to_user
        ))
        self.log_info(
            f"В чате {chat_id} владелец сменился с {from_user} на {to_user}"
        )