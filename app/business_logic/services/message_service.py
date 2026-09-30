import random
from datetime import date
from uuid import UUID

from app.business_logic.psw_manager import PasswordManager
from app.business_logic.redis_adapter import VerifyCodeStorage, Cache
from app.business_logic.websocket.broker import WSBroker
from app.data_layer.models import User, UserInfo
from app.data_layer.models.events import EventType
from app.business_logic.unit_of_work import UnitOfWork
from app.shared.dto import UserDtoSave, MessageDtoSave
from app.shared.dto.message import MessageDtoGet, MessageAttachmentDtoGet
from app.shared.dto.user import UserDtoGet, UserDtoBriefGet, RegisterDtoGet, UserDtoUpdateDefaultInfo, \
    UserDtoUpdateExtendedInfo
from app.shared.log_config import LogMixin
from app.shared.config import get_config, AppMode, BaseConfig
from collections import deque

def _get_config() -> BaseConfig:
    return get_config()


class MessageService(LogMixin):
    """Сервис для управления сообщениями"""
    def __init__(
            self,
            uow: UnitOfWork,
            cache: Cache,
            broker: WSBroker
    ):
        self._uow = uow
        self._cache = cache
        self._broker = broker

    async def send_and_save_message(self, msg_dto: MessageDtoSave) -> MessageDtoGet:
        """Сохранения сообщения"""
        async with self._uow as uow:
            msg_orm = await uow.msg_repo.save(msg_dto)
            self.log_info(f'Сообщение пользователя {msg_dto.sender_id} было успешно сохранено в чат {msg_dto.chat_id}')
            response = MessageDtoGet(**msg_orm.to_dict())
            if _get_config().mode not in (AppMode.DEV,):
                uow.add_event(
                    event_name='Save new message',
                    payload=response.model_dump(),
                    event_type=EventType.NEW_MESSAGE
                )
                self.log_info(f'Событие {EventType.NEW_MESSAGE} зарегистрировано')
        is_saved = await self._cache.save_chat_msg_info(response)
        if not is_saved:
            self.log_warning(f'Сообщение в чате {msg_dto.chat_id} было успешно сохранено')
        await self._broker.publish_to_chat(
            action_type='CREATE_MESSAGE',
            chat_id=msg_dto.chat_id,
            data=response.model_dump(mode='json')
        )
        return response

    async def get_message_by_chat(self, msg_date: date, chat_id: UUID) -> list[MessageDtoGet]:
        """Получение сообщения в чате"""
        cached_data = await self._cache.get_chat_msg_info(chat_id, msg_date)
        messages_dto: list[MessageDtoGet] = []
        if cached_data:
            return [MessageDtoGet(**msg) for msg in cached_data]
        async with self._uow as uow:
            messages_orm = await uow.msg_repo.get_message_by_chat(msg_date, chat_id)
        for msg in messages_orm:
            msg_dto = MessageDtoGet(**msg.to_dict())
            messages_dto.append(msg_dto)
            is_saved = await self._cache.save_chat_msg_info(msg_dto)
            if not is_saved:
                self.log_warning(f'Сообщение в чате {msg_dto.chat_id} было успешно сохранено в кеше')
        return messages_dto

    async def get_message_by_sender(self, msg_date: date, sender_id: str) -> dict[UUID, list[MessageDtoGet]]:
        """Получение всех сообщений отправителя"""
        async with self._uow as uow:
            msgs_orm = await uow.msg_repo.get_message_by_sender(msg_date, sender_id)
            response = {
                chat_id: [MessageDtoGet(**msg.to_dict()) for msg in msgs]
                for chat_id, msgs in msgs_orm.items()
            }
            return response

    async def get_file_by_id(self, file_id: UUID) -> MessageAttachmentDtoGet:
        """Получение файлов для сообщения"""
        async with self._uow as uow:
            msg_orm = await uow.msg_repo.get_file_by_id(file_id)
            response = MessageAttachmentDtoGet(**msg_orm.to_dict())
            return response

    async def delete_message(self, message_id: UUID) -> MessageDtoGet:
        """Удаление сообщения"""
        async with self._uow as uow:
            message = await uow.msg_repo.delete(message_id)
            response = MessageDtoGet(**message.to_dict())
        await self._broker.publish_to_chat(
            action_type='DELETE_MESSAGE',
            chat_id=response.chat_id,
            data=response.model_dump(mode='json')
        )
        return response