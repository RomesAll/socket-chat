from datetime import date
from uuid import UUID
from app.business_logic.encrypte_manager import SymmetricEncode
from app.business_logic.redis_adapter import Cache
from app.business_logic.websocket.broker import WSBroker
from app.data_layer.models.events import EventType
from app.business_logic.unit_of_work import UnitOfWork
from app.shared.dto import MessageDtoSave
from app.shared.dto.message import (
    MessageDtoGetWithBodyEncrypted,
    MessageAttachmentDtoGet,
    MessageDtoCreate,
    MessageDtoGetWithBodyDecrypted
)
from app.shared.log_config import LogMixin
from app.shared.config import get_config, AppMode, BaseConfig


def _get_config() -> BaseConfig:
    return get_config()


class MessageService(LogMixin):
    """Сервис для управления сообщениями"""
    def __init__(
            self,
            uow: UnitOfWork,
            cache: Cache,
            broker: WSBroker,
            cipher: SymmetricEncode
    ):
        self._uow = uow
        self._cache = cache
        self._broker = broker
        self._cipher = cipher

    async def send_and_save_message(self, msg_dto: MessageDtoSave) -> MessageDtoGetWithBodyDecrypted:
        """Сохранения сообщения"""
        encrypted = str(self._cipher.encrypt(msg_dto.body))
        create_dto = MessageDtoCreate(
            **msg_dto.model_dump(),
            body_encrypted=encrypted
        )
        async with self._uow as uow:
            msg_orm = await uow.msg_repo.save(create_dto)
            self.log_info(f'Сообщение пользователя {msg_dto.sender_id} было успешно сохранено в чат {msg_dto.chat_id}')
            msg_dto_body_enc = MessageDtoGetWithBodyEncrypted(**msg_orm.to_dict())
            if _get_config().mode not in (AppMode.DEV,):
                uow.add_event(
                    event_name='Save new message',
                    payload=msg_dto_body_enc.model_dump(),
                    event_type=EventType.SEND_MESSAGE_IN_CHAT
                )
                self.log_info(f'Событие {EventType.SEND_MESSAGE_IN_CHAT} зарегистрировано')
        is_saved = await self._cache.save_chat_msg_info(msg_dto_body_enc)
        if not is_saved:
            self.log_warning(f'Сообщение в чате {msg_dto.chat_id} было успешно сохранено')
        message_result = MessageDtoGetWithBodyDecrypted(
            **msg_dto_body_enc.model_dump(),
            body=self._cipher.decrypt(msg_dto_body_enc.body_encrypted.encode())
        )
        await self._broker.publish_to_chat(
            action_type='CREATE_MESSAGE',
            chat_id=msg_dto.chat_id,
            data=message_result.model_dump(mode='json')
        )
        return message_result

    async def get_message_by_chat(self, msg_date: date, chat_id: UUID) -> list[MessageDtoGetWithBodyDecrypted]:
        """Получение сообщения в чате"""
        cached_data = await self._cache.get_chat_msg_info(chat_id, msg_date)
        messages_dto: list[MessageDtoGetWithBodyDecrypted] = []
        if cached_data:
            return [
                MessageDtoGetWithBodyDecrypted(
                    **msg, body=self._cipher.decrypt(msg['body_encrypted'])
                )
                for msg in cached_data
            ]
        async with self._uow as uow:
            messages_orm = await uow.msg_repo.get_message_by_chat(msg_date, chat_id)
        for msg in messages_orm:
            msg_dto = MessageDtoGetWithBodyDecrypted(
                **msg.to_dict(),
                body=self._cipher.decrypt(msg['body_encrypted'])
            )
            messages_dto.append(msg_dto)
            msg_dto_body_enc = MessageDtoGetWithBodyEncrypted(**msg.to_dict())
            is_saved = await self._cache.save_chat_msg_info(msg_dto_body_enc)
            if not is_saved:
                self.log_warning(f'Сообщение в чате {msg_dto.chat_id} было успешно сохранено в кеше')
        return messages_dto

    async def get_message_by_sender(self, msg_date: date, sender_id: str) -> dict[UUID, list[MessageDtoGetWithBodyDecrypted]]:
        """Получение всех сообщений отправителя"""
        async with self._uow as uow:
            msgs_orm = await uow.msg_repo.get_message_by_sender(msg_date, sender_id)
            response = {
                chat_id: [
                    MessageDtoGetWithBodyDecrypted(
                        **msg.to_dict(),
                        body=self._cipher.decrypt(msg['body_encrypted'])
                    )
                    for msg in msgs
                ]
                for chat_id, msgs in msgs_orm.items()
            }
            return response

    async def get_file_by_id(self, file_id: UUID) -> MessageAttachmentDtoGet:
        """Получение файлов для сообщения"""
        async with self._uow as uow:
            msg_orm = await uow.msg_repo.get_file_by_id(file_id)
            response = MessageAttachmentDtoGet(**msg_orm.to_dict())
            return response

    async def delete_message(self, message_id: UUID) -> MessageDtoGetWithBodyDecrypted:
        """Удаление сообщения"""
        async with self._uow as uow:
            message = await uow.msg_repo.delete(message_id)
            response = MessageDtoGetWithBodyDecrypted(
                **message.to_dict(),
                body=self._cipher.decrypt(message.body_encrypted)
            )
        await self._broker.publish_to_chat(
            action_type='DELETE_MESSAGE',
            chat_id=response.chat_id,
            data=response.model_dump(mode='json')
        )
        return response