from datetime import datetime, date, timedelta
from uuid import UUID
from sqlalchemy import select
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

    async def get_message_by_chat(self, date_limit: date, chat_id: UUID) -> list[MessageEncryptedReadDTO]:
        """
        Получить сообщения в чате.

        :param date_limit: Дата выборки сообщений.
        :param chat_id: Id чата.
        :return: Список ORM-моделей Message
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
        results = await self.session.scalars(stmt)
        return [MessageEncryptedReadDTO(**msg.to_dict()) for msg in results.all()]

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

    async def update_message(self, message_id: UUID, new_encr_msg: str) -> Message:
        """Обновить сообщение отправителя."""
        msg = await self.get_record_by_id(message_id)
        msg.body_encrypted = new_encr_msg
        await self.session.flush()
        return msg