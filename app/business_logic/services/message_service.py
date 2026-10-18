from datetime import date
from uuid import UUID
from app.business_logic.mappers.message_mapper import MessageMapper
from app.business_logic.unit_of_work import UnitOfWork
from app.domain.events import MessageSent, MessageEdited, MessageDeleted
from app.infrastructure.redis import ChatMessageCache
from app.shared.dto.message import (
    MessageEncryptedReadDTO,
    MessageEncryptedSenderGroupChat,
    MessageAttachmentSaveDTO,
    MessageAttachmentGetDTO,
    MessageEncryptedSavedDTO,
    MessageEncryptedGetDTO,
)
from app.shared.log_config import LogMixin


class MessageService(LogMixin):
    """Сервис для управления сообщениями и вложениями."""

    def __init__(self, uow: UnitOfWork, mapper: MessageMapper, cache: ChatMessageCache):
        self._uow = uow
        self._mapper = mapper
        self._cache = cache

    async def get_message_by_chat(self, date_limit: date, chat_id: UUID) -> list[MessageEncryptedGetDTO]:
        """Получить сообщения в чате"""
        orm_messages = await self._uow.msg_repo.get_message_by_chat_with_rel(date_limit, chat_id)
        dto_messages = self._mapper.to_read_dtos_with_rel(orm_messages)
        return dto_messages

    async def get(self, message_id: UUID) -> MessageEncryptedReadDTO:
        """
        Получить сообщение по ID.

        :exception RecordNotFound если сообщение не найдено.
        """
        message_orm = await self._uow.msg_repo.get_record_by_id(message_id)
        return self._mapper.to_read_dto(message_orm)

    async def find(self, message_id: UUID) -> MessageEncryptedReadDTO | None:
        """
        Найти сообщение по ID.

        :return: DTO или None, если сообщение не найдено.
        """
        message_orm = await self._uow.msg_repo.find_by_id(message_id)
        if message_orm is None:
            return None
        return self._mapper.to_read_dto(message_orm)

    async def get_by_chat(self, chat_id: UUID, date_limit: date) -> list[MessageEncryptedReadDTO]:
        """
        Получить историю сообщения чата за указанную дату.

        Алгоритм:\n
        - Делегировать выборку в репозиторий.
        - Вернуть список DTO с зашифрованным телом.
        """
        cached = await self._cache.get_history(chat_id, date_limit)
        if cached:
            return cached

        msg_dto = await self._uow.msg_repo.get_message_by_chat(date_limit, chat_id)
        self._uow.add_after_commit(lambda : self._cache.push(msg_dto))
        return msg_dto

    async def get_by_sender(self, sender_id: str, date_limit: date) -> MessageEncryptedSenderGroupChat:
        """
        Получить сообщения отправителя за определенное время, сгруппированные по чатам.
        """
        return await self._uow.msg_repo.get_message_by_sender(date_limit, sender_id)

    async def save(self, message_dto: MessageEncryptedSavedDTO) -> MessageEncryptedReadDTO:
        """
        Сохранить новое сообщение.

        Алгоритм:\n
        - Маппинг из DTO с открытым текстом -> DTO с зашифрованным.
        - Сохранение сообщения в сессию БД.
        - Маппинг в DTO из ORM с расшифровкой.

        :param message_dto: DTO с открытым текстом.
        :return: DTO с расшифрованным текстом.
        """
        message_orm = await self._uow.msg_repo.save(message_dto)
        saved_message = self._mapper.to_read_dto(message_orm)
        self._uow.add_event(MessageSent(
            message=saved_message
        ))
        self.log_info(
            f"Создано сообщение {saved_message.id} в чате {saved_message.chat_id}"
        )
        return saved_message

    async def update_body(self, message_id: UUID, new_encr_msg: bytes) -> MessageEncryptedReadDTO:
        """
        Обновить тело сообщения.

        Алгоритм:\n
        - Зашифровать новый текст через маппер.
        - Обновить тело в БД.
        - Пометить сообщение как изменённое.
        - Маппинг ORM в DTO с расшифровкой.

        :param message_id: ID сообщения.
        :param new_encr_msg: Новый открытый текст.
        :return: DTO с расшифрованным текстом.
        """
        message_orm = await self._uow.msg_repo.update_message(
            message_id, new_encr_msg,
        )
        message_orm = await self._uow.msg_repo.set_is_edited(message_orm.id)
        updated_message = self._mapper.to_read_dto(message_orm)
        self._uow.add_event(MessageEdited(
            message_id=message_id,
            chat_id=message_orm.chat_id,
            new_body_encrypted=new_encr_msg
        ))
        self.log_info(f"Обновлено сообщение {updated_message.id}")
        return updated_message

    async def delete(self, message_id: UUID) -> MessageEncryptedReadDTO:
        """
        Удалить сообщение.
        """
        message_orm = await self._uow.msg_repo.delete(message_id)
        deleted_message = self._mapper.to_read_dto(message_orm)
        self._uow.add_event(MessageDeleted(
            message_id=message_id,
            chat_id=message_orm.chat_id,
        ))
        self.log_info(f"Удалено сообщение {deleted_message.id}")
        return deleted_message

    async def get_attachment(self, attachment_id: UUID) -> MessageAttachmentGetDTO:
        """
        Получить вложение по ID.
        :exception RecordNotFound.
        """
        attachment_orm = await self._uow.msg_attach_repo.get_record_by_id(attachment_id)
        return self._mapper.attachment_to_dto(attachment_orm)

    async def get_attachments(self, message_id: UUID) -> list[MessageAttachmentGetDTO]:
        """Получить вложения сообщения."""
        return await self._uow.msg_attach_repo.get_files_message(message_id)

    async def add_attachment(self, attachment_dto: MessageAttachmentSaveDTO) -> MessageAttachmentGetDTO:
        """
        Добавить вложение к сообщению.
        """
        attachment_orm = await self._uow.msg_attach_repo.save(attachment_dto)
        saved_attachment = self._mapper.attachment_to_dto(attachment_orm)
        self.log_info(
            f"Добавлено вложение {saved_attachment.id} "
            f"к сообщению {saved_attachment.message_id}"
        )
        return saved_attachment

    async def delete_attachment(self, attachment_id: UUID) -> MessageAttachmentGetDTO:
        """Удалить вложение."""
        attachment_orm = await self._uow.msg_attach_repo.delete(attachment_id)
        deleted_attachment = self._mapper.attachment_to_dto(attachment_orm)
        self.log_info(f"Удалено вложение {deleted_attachment.id}")
        return deleted_attachment