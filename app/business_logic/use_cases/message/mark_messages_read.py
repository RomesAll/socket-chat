from uuid import UUID
from app.business_logic.exceptions import PermissionError
from app.business_logic.services import ChatService, MessageService
from app.business_logic.unit_of_work import UnitOfWork
from app.infrastructure.redis import UnreadCache
from app.infrastructure.websocket import WSBroker
from app.shared.dto.chat import ChatMemberDTO
from app.shared.log_config import LogMixin


class MarkMessagesReadUseCase(LogMixin):
    """
    Отметить сообщения чата прочитанными.

    Сценарий:
    - Проверить, что актор — участник чата.
    - Проверить, что сообщение — в этом чате.
    - Обновить last_read_message_id.
    - Сбросить счётчик непрочитанных.
    - Записать audit-событие.
    """

    def __init__(
        self,
        chat_service: ChatService,
        message_service: MessageService,
        unread_cache: UnreadCache,
        ws_broker: WSBroker,
        uow: UnitOfWork,
    ):
        self._chat_service = chat_service
        self._message_service = message_service
        self._unread_cache = unread_cache
        self._ws_broker = ws_broker
        self._uow = uow

    async def execute(
        self,
        chat_id: UUID,
        message_id: UUID,
        actor_id: str,
    ) -> ChatMemberDTO:
        # Проверить права
        is_member = await self._chat_service.is_member(chat_id, actor_id)
        if not is_member:
            self.log_warning(
                f"Пользователь {actor_id} не участник чата {chat_id}"
            )
            raise PermissionError(
                f"Пользователь {actor_id} не участник чата {chat_id}"
            )

        # Проверить сообщение в чате
        message = await self._message_service.get(message_id)
        if message.chat_id != chat_id:
            raise PermissionError(
                f"Сообщение {message_id} не из чата {chat_id}"
            )

        # Обновить last_read_message_id
        member = await self._chat_service.set_last_read(
            chat_id=chat_id,
            user_id=actor_id,
            message_id=message_id,
        )

        # Сбросить счётчик непрочитанных
        self._uow.add_after_commit(
            lambda: self._unread_cache.reset(
                chat_id=chat_id,
                user_id=actor_id,
            )
        )

        self.log_info(
            f"Пользователь {actor_id} прочитал чат {chat_id} "
            f"до сообщения {message_id}"
        )
        return member