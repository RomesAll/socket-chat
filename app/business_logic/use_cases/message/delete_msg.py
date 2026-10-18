from datetime import datetime, timezone
from uuid import UUID
from app.business_logic.exceptions import PermissionError
from app.business_logic.services import ChatService, MessageService
from app.business_logic.unit_of_work import UnitOfWork
from app.domain.events.audit import AuditEvent, Context
from app.domain.events.enums import ActionType
from app.infrastructure.websocket import WSBroker
from app.shared.dto.audit import RequestMeta
from app.shared.log_config import LogMixin


class DeleteMessageUseCase(LogMixin):
    """
    Удалить сообщение.

    Сценарий:
    - Проверить права (автор или админ).
    - Удалить сообщение.
    - Опубликовать в WebSocket.
    - Записать audit-событие.
    """

    def __init__(
        self,
        message_service: MessageService,
        chat_service: ChatService,
        ws_broker: WSBroker,
        uow: UnitOfWork,
    ):
        self._message_service = message_service
        self._chat_service = chat_service
        self._ws_broker = ws_broker
        self._uow = uow

    async def execute(
        self,
        message_id: UUID,
        actor_id: str,
        request_meta: RequestMeta,
    ):
        time_now = datetime.now(tz=timezone.utc)

        # Получить сообщение
        message = await self._message_service.get(message_id)

        # Проверить права
        is_author = message.sender_id == actor_id
        is_admin = await self._chat_service.is_admin(message.chat_id, actor_id)

        if not is_author and not is_admin:
            self.log_warning(
                f"Пользователь {actor_id} пытался удалить сообщение {message_id}"
            )
            raise PermissionError(
                f"Пользователь {actor_id} не может удалить сообщение {message_id}"
            )

        # Удалить сообщение
        deleted = await self._message_service.delete(message_id)

        # Отправить событие по ws
        self._uow.add_after_commit(
            lambda: self._ws_broker.publish_to_chat(
                action_type="message_deleted",
                chat_id=message.chat_id,
                data={"id": str(message_id)},
            )
        )

        # Сохранить событие
        self._uow.add_event(AuditEvent(
            actor_type=ActionType.DELETE_MESSAGE_IN_CHAT,
            actor_id=actor_id,
            target_id=str(message_id),
            old_data={
                "chat_id": str(message.chat_id),
                "sender_id": message.sender_id,
                "type": message.type.value,
            },
            new_data=None,
            context=Context(
                ip=request_meta.ip,
                user_agent=request_meta.user_agent,
                source=request_meta.source,
            ),
            occurred_at=time_now,
        ))

        self.log_info(
            f"Пользователь {actor_id} удалил сообщение {message_id}"
        )