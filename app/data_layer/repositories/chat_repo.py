from uuid import UUID
from sqlalchemy import select, and_, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload
from app.data_layer.exceptions import RecordNotFound
from app.data_layer.repositories.base import BaseRepository
from app.data_layer.models import Chat, ChatMember
from app.shared.dto.chat import ChatDtoSave, ChatMemberDtoSave, ChatMemberDtoUpdate


class ChatRepository(BaseRepository[Chat]):
    """Репозиторий для работы с чатами"""
    MODEL: type[Chat] = Chat
    CHAT_MEMBER_MODEL: type[ChatMember] = ChatMember

    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self.MAPPING_DTO_ORM_SAVE.update({
            ChatDtoSave: Chat,
            ChatMemberDtoSave: ChatMember
        })

    async def get_chat_by_id(self, chat_id: UUID, with_relation: bool = False) -> Chat:
        """Получение чата по id"""
        options = None
        if with_relation:
            options = self._with_chat_options()
        result = await self._get_by_id(chat_id, options)
        return result

    async def get_user_chats(self, user_id: str) -> list[ChatMember]:
        """Получение информации о чатах, в которых состоит пользователь"""
        stmt = (
            select(self.CHAT_MEMBER_MODEL)
            .where(self.CHAT_MEMBER_MODEL.user_id == user_id)
            .options(joinedload(self.CHAT_MEMBER_MODEL.chat))
        )
        sqla_obj = await self.session.execute(stmt)
        chat_member = sqla_obj.scalars().all()
        return list(chat_member)


    async def get_chat_by_room(self, room_id: UUID, with_relation: bool = False) -> list[Chat]:
        """Получение чата по id комнаты"""
        stmt = (
            select(self.MODEL)
            .where(self.MODEL.room_id == room_id)
        )
        if with_relation:
            stmt = stmt.options(*self._with_chat_options())
        sqla_obj = await self.session.execute(stmt)
        results = sqla_obj.scalars().all()
        return list(results)

    async def get_chat_members(self, chat_id: UUID, with_relation: bool = False) -> list[ChatMember]:
        """Получение участников чата"""
        stmt = (
            select(self.CHAT_MEMBER_MODEL)
            .where(self.CHAT_MEMBER_MODEL.chat_id == chat_id)
        )
        if with_relation:
            stmt = stmt.options(*self._with_chat_options())
        sqla_obj = await self.session.execute(stmt)
        results = sqla_obj.scalars().all()
        return list(results)

    async def add_chat_member(self, chat_member: ChatMemberDtoSave) -> ChatMember:
        """Добавление участника чата"""
        new_chat_member = self.CHAT_MEMBER_MODEL(
            **chat_member.model_dump()
        )
        self.session.add(new_chat_member)
        return new_chat_member

    async def delete_chat_member(self, chat_id: UUID, user_id: str) -> int:
        """Удаление участника чата"""
        stmt = (
            delete(self.CHAT_MEMBER_MODEL)
            .where(and_(
                self.CHAT_MEMBER_MODEL.user_id == user_id,
                self.CHAT_MEMBER_MODEL.chat_id == chat_id,
            ))
            .returning(self.CHAT_MEMBER_MODEL.user_id)
        )
        sqla_obj = await self.session.execute(stmt)
        deleted = sqla_obj.scalars().all()
        if not deleted:
            raise RecordNotFound(chat_id, self.MODEL, 'id')
        return len(deleted)

    async def update_member(self, chat_id: UUID, user_id: str, update_member: ChatMemberDtoUpdate) -> ChatMember:
        """Обновления учатсника чата"""
        raw_data = update_member.model_dump(
            exclude_unset=True,
            exclude_none=True,
            exclude_defaults=True
        )
        stmt = (
            select(self.CHAT_MEMBER_MODEL)
            .where(
                and_(
                    self.CHAT_MEMBER_MODEL.chat_id == chat_id,
                    self.CHAT_MEMBER_MODEL.user_id == user_id
                )
            )
        )
        sqla_obj = await self.session.execute(stmt)
        member_info = sqla_obj.scalar_one_or_none()
        if not member_info:
            raise RecordNotFound(f'чат={chat_id}, user={user_id}', self.MODEL, 'id')
        for k, v in raw_data.items():
            setattr(member_info, k, v)
        return member_info

    def _with_chat_options(self):
        """Получение relation для жадной загрузки"""
        return [
            selectinload(self.MODEL.members),
        ]

    def _with_chat_members_options(self):
        """Получение relation для жадной загрузки"""
        return [
            joinedload(self.CHAT_MEMBER_MODEL.chat),
        ]