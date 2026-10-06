from typing import Sequence
from uuid import UUID
from sqlalchemy import select, and_, delete
from sqlalchemy.orm import selectinload, joinedload
from app.data_layer.exceptions import RecordNotFound
from app.data_layer.repositories.base import BaseRepository
from app.data_layer.models import Chat, ChatMember
from app.shared.dto.chat import ChatMemberDtoSave, ChatMemberDtoUpdate


class ChatRepository(BaseRepository[Chat]):
    """Репозиторий для работы с чатами"""
    MODEL: type[Chat] = Chat
    CHAT_MEMBER_MODEL: type[ChatMember] = ChatMember

    async def get_user_chats(self, user_id: str) -> Sequence[ChatMember]:
        """
        Получение информации о чатах, в которых состоит пользователь
        :param user_id: идентификатор пользователя
        :return: Sequence объекты orm модели ChatMember
        """
        stmt = (
            select(self.CHAT_MEMBER_MODEL)
            .where(self.CHAT_MEMBER_MODEL.user_id == user_id)
        )
        results = await self.session.scalars(stmt)
        return results.all()

    async def get_chat_by_room(self, room_id: UUID) -> Sequence[Chat]:
        """
        Получение информации о чатах в комнате
        :param room_id: идентификатор комнаты
        :return: Sequence объекты orm модели Chat
        """
        stmt = (
            select(self.MODEL)
            .where(self.MODEL.room_id == room_id)
        )
        results = await self.session.scalars(stmt)
        return results.all()

    async def get_chat_members(self, chat_id: UUID) -> Sequence[ChatMember]:
        """
        Получение информации об участниках чата
        :param chat_id: идентификатор чата
        :return: Sequence объекты orm модели Chat
        """
        stmt = (
            select(self.CHAT_MEMBER_MODEL)
            .where(self.CHAT_MEMBER_MODEL.chat_id == chat_id)
        )
        results = await self.session.scalars(stmt)
        return results.all()

    async def add_chat_member(self, chat_id: UUID, user_id: str) -> ChatMember:
        """
        Добавление нового участника в чат
        :param user_id: идентификатор пользователя
        :param chat_id: идентификатор чата
        :return: новый объект orm модели ChatMember
        """
        new_chat_member = self.CHAT_MEMBER_MODEL(
            chat_id=chat_id,
            user_id=user_id
        )
        self.session.add(new_chat_member)
        return new_chat_member

    async def remove_chat_member(self, chat_id: UUID, user_id: str) -> ChatMember:
        """
        Удалить участника из комнаты
        :param user_id: идентификатор пользователя
        :param chat_id: идентификатор чата
        :return: удаленный объекты orm модели ChatMember
        """
        stmt_exist = (
            select(self.CHAT_MEMBER_MODEL)
            .where(
                self.CHAT_MEMBER_MODEL.user_id == user_id,
                self.CHAT_MEMBER_MODEL.chat_id == chat_id
            )
        )
        chat_member = await self.session.scalar(stmt_exist)
        if not chat_member:
            raise RecordNotFound(
                [user_id, chat_id],
                self.CHAT_MEMBER_MODEL.__tablename__,
                'user_id, chat_id'
            )
        await self.session.delete(chat_member)
        return chat_member

    async def update_member(
            self, chat_id: UUID, user_id: str, update_member: ChatMemberDtoUpdate
    ) -> ChatMember:
        """
        Обновления участника чата
        :param user_id: идентификатор пользователя
        :param chat_id: идентификатор чата
        :param update_member: dto с полями для обновления
        :return: обновленный объекты orm модели ChatMember
        """
        raw_data = update_member.model_dump(
            exclude_unset=True,
            exclude_none=True,
            exclude_defaults=True
        )
        stmt_exist = (
            select(self.CHAT_MEMBER_MODEL)
            .where(
                self.CHAT_MEMBER_MODEL.user_id == user_id,
                self.CHAT_MEMBER_MODEL.chat_id == chat_id
            )
        )
        chat_member = await self.session.scalar(stmt_exist)
        if not chat_member:
            raise RecordNotFound(
                [user_id, chat_id],
                self.CHAT_MEMBER_MODEL.__tablename__,
                'user_id, chat_id'
            )
        for k, v in raw_data.items():
            setattr(chat_member, k, v)
        return chat_member