from datetime import datetime, date, timedelta
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import joinedload, selectinload
from app.infrastructure.database.exceptions import RecordNotFound
from app.infrastructure.database.repositories.base.base_repo import (
    BaseGetRepository,
    BaseSaveRepository,
    BaseDeleteRepository
)
from app.infrastructure.database.models import Message
from app.shared.dto.message import (
    MessageEncryptedSavedDTO,
    MessageEncryptedReadDTO,
    MessageEncryptedSenderGroupChat
)


class MessageRepository(
    BaseGetRepository[Message],
    BaseSaveRepository[Message, MessageEncryptedSavedDTO],
    BaseDeleteRepository[Message]
):
    """Репозиторий для работы с сообщениями"""

    MODEL: type[Message] = Message

    async def get_message_by_chat_with_rel(
            self,
            chat_id: UUID,
            limit: int = 50,
            before_id: UUID | None = None
    ) -> list[Message]:
        """Получить сообщения в чате с relationship (пагинация через limit/before_id)"""
        stmt = select(self.MODEL).where(self.MODEL.chat_id == chat_id)
        if before_id:
            cursor_msg = await self.session.get(self.MODEL, before_id)
            if cursor_msg:
                stmt = stmt.where(self.MODEL.created_at < cursor_msg.created_at)

        stmt = (
            stmt
            .order_by(self.MODEL.created_at.desc())
            .limit(limit)
            .options(
                joinedload(self.MODEL.reply_to),
                joinedload(self.MODEL.forwarded_from).selectinload(Message.files),
                selectinload(self.MODEL.files)
            )
        )
        result = await self.session.scalars(stmt)
        messages = list(result.all())
        messages.reverse()
        return messages

    async def get_msg_by_id(self, msg_id: UUID) -> Message:
        stmt = (
            select(self.MODEL)
            .where(
                self.MODEL.id == msg_id,
            )
            .options(
                joinedload(self.MODEL.reply_to),
                joinedload(self.MODEL.forwarded_from).selectinload(Message.files),
                selectinload(self.MODEL.files)
            )
        )
        result = await self.session.scalar(stmt)
        if not result:
            raise RecordNotFound([msg_id], 'message', 'id')
        return result

    async def get_previous_message(self, chat_id: UUID, before_date: datetime) -> Message | None:
        """Получить preview сообщения"""
        stmt = (
            select(self.MODEL)
            .where(
                self.MODEL.chat_id == chat_id,
                self.MODEL.created_at < before_date
            )
            .order_by(self.MODEL.created_at.desc())
            .limit(1)
        )
        return await self.session.scalar(stmt)

    async def get_message_by_chat(self, date_limit: date, chat_id: UUID) -> list[Message]:
        """
        Получить сообщения в чате (чистый ORM для маппера).
        """
        start = datetime.combine(date_limit, datetime.min.time())
        end = start + timedelta(days=1)
        stmt = (
            select(self.MODEL)
            .where(
                self.MODEL.chat_id == chat_id,
                self.MODEL.created_at >= start,
                self.MODEL.created_at < end
            )
            .order_by(self.MODEL.created_at)
        )
        result = await self.session.scalars(stmt)
        return list(result.all())

    async def get_message_by_sender(self, date_limit: date, sender_id: str) -> MessageEncryptedSenderGroupChat:
        """
        Получить сообщения отправителя, сгруппированных по чатам.

        :param date_limit: Дата сообщений.
        :param sender_id: Id отправителя.
        :return: Ключ - id чата, значение - список сообщений.
        """
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
        results = await self.session.scalars(stmt)
        messages = results.all()
        grouped: dict[UUID, list[MessageEncryptedReadDTO]] = {}
        for msg in messages:
            grouped.setdefault(msg.chat_id, []).append(
                MessageEncryptedReadDTO(**msg.to_dict())
            )
        result = MessageEncryptedSenderGroupChat(
            sender_id=sender_id,
            date_limit=date_limit,
            count_chats=len(grouped.keys()),
            chats=grouped
        )
        return result

    async def set_is_edited(self, message_id: UUID) -> Message:
        """Сделать сообщение измененным"""
        msg = await self.get_record_by_id(message_id)
        if not msg.is_edited:
            msg.is_edited = True
            await self.session.flush()
        return msg

    async def update_message(self, message_id: UUID, new_encr_msg: bytes) -> Message:
        """Обновить сообщение отправителя."""
        msg = await self.get_record_by_id(message_id)
        msg.body_encrypted = new_encr_msg
        await self.session.flush()
        return msg