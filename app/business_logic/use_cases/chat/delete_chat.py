from datetime import datetime, timezone
from uuid import UUID
from app.business_logic.services import ChatService
from app.business_logic.unit_of_work import UnitOfWork
from app.domain.events.audit import AuditEvent, Context
from app.domain.events.enums import ActionType
from app.infrastructure.websocket import WSBroker
from app.shared.dto.audit import RequestMeta
from app.shared.dto.enums import ChatType, ChatRole
from app.shared.log_config import LogMixin
from app.business_logic.exceptions import PermissionError


class DeleteChatUseCase(LogMixin):
    """
    Удалить чат (комнату). При удалении каскадно удаляются участники,
    сообщения и меди-файлы в сообщения.
    """

    def __init__(
        self,
        ws_broker: WSBroker,
        chat_service: ChatService,
        uow: UnitOfWork
    ):
        self._ws_broker = ws_broker
        self._chat_service = chat_service
        self._uow = uow

    async def execute(
            self,
            chat_id: UUID,
            actor_id: str,
            request_meta: RequestMeta
    ):
        time_now = datetime.now(tz=timezone.utc)

        # Получить информацию
        chat_info = await self._chat_service.get(chat_id)
        member_info = await self._chat_service.get_member(chat_id, actor_id)
        chat_members = await self._chat_service.get_members(chat_id)

        # Запрет на удаление Избранного
        if chat_info.type == ChatType.FAVORITES:
            raise PermissionError("Нельзя удалить чат «Избранное»")

        # Проверка прав для комнаты
        if chat_info.type == ChatType.ROOM and member_info.role != ChatRole.OWNER:
            raise PermissionError("Только владелец может удалить комнату")

        member_ids = [m.user_id for m in chat_members]

        # Удалить чат
        await self._chat_service.delete(chat_id)

        # Сохранить событие
        self._uow.add_event(AuditEvent(
            actor_type=ActionType.DELETE_CHAT,
            actor_id=actor_id,
            target_id=str(chat_id),
            old_data=None,
            new_data=None,
            context=Context(
                ip=request_meta.ip,
                user_agent=request_meta.user_agent,
                source=request_meta.source,
            ),
            occurred_at=time_now,
        ))

        # Отправить событие по ws
        self._uow.add_after_commit(
            lambda: self._ws_broker.publish_delete_chat(
                chat_id=chat_id,
                member_ids=member_ids,
            )
        )