from datetime import datetime, date, timedelta
from uuid import UUID
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload, joinedload
from app.data_layer.repositories.base import BaseRepository
from app.data_layer.models import Message, MessageAttachment
from app.shared.dto.message import MessageDtoSave, MessageDtoUpdate


class MessageRepository(BaseRepository[Message]):
    """Репозиторий для работы с сообщениями"""
    MODEL: type[Message] = Message
    MESSAGE_ATTACHMENT_MODEL: type[MessageAttachment] = MessageAttachment

    async def get_message_by_chat(self, date_limit: date, chat_id: UUID, with_relation: bool = False) -> list[Message]:
        """Получение сообщений по чату"""
        start = datetime.combine(date_limit, datetime.min.time())
        end = start + timedelta(days=1)
        stmt = (
            select(self.MODEL)
            .where(and_(
                self.MODEL.chat_id == chat_id,
                self.MODEL.created_at >= start,
                self.MODEL.created_at < end
            ))
            .order_by(self.MODEL.created_at)
        )
        if with_relation:
            stmt = stmt.options(*self._with_msg_options())
        sqla_obj = await self.session.execute(stmt)
        messages = sqla_obj.scalars().all()
        return list(messages)

    async def get_message_by_sender(self, date_limit: date, sender_id: str, with_relation: bool = False) -> dict[UUID, list[Message]]:
        """Получение сообщений отправителя"""
        start = datetime.combine(date_limit, datetime.min.time())
        end = start + timedelta(days=1)
        stmt = (
            select(self.MODEL)
            .where(
                self.MODEL.sender_id == sender_id,
                self.MODEL.created_at >= start,
                self.MODEL.created_at < end
            )
            .order_by(self.MODEL.created_at)
        )
        if with_relation:
            stmt = stmt.options(*self._with_msg_options())
        sqla_obj = await self.session.execute(stmt)
        messages = sqla_obj.scalars().all()
        grouped: dict[UUID, list[Message]] = {}
        for msg in messages:
            grouped.setdefault(msg.chat_id, []).append(msg)
        return grouped

    async def get_file_by_id(self, file_id: UUID, with_relation: bool = False) -> MessageAttachment:
        """Получение файлов по id"""
        stmt = (
            select(self.MESSAGE_ATTACHMENT_MODEL)
            .where(self.MESSAGE_ATTACHMENT_MODEL.id == file_id)
        )
        if with_relation:
            stmt = stmt.options(*self._with_msg_attachment_options())
        sqla_obj = await self.session.execute(stmt)
        msg_file = sqla_obj.scalar_one_or_none()
        if not msg_file:
            raise Exception
        return msg_file

    def _with_msg_options(self):
        """Получение relation для жадной загрузки"""
        return [
            selectinload(self.MODEL.message_file),
        ]

    def _with_msg_attachment_options(self):
        """Получение relation для жадной загрузки"""
        return [
            joinedload(self.MESSAGE_ATTACHMENT_MODEL.message_info),
        ]