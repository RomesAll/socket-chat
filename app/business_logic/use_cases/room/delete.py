from datetime import datetime, timezone
from uuid import UUID
from app.business_logic.exceptions import PermissionError
from app.business_logic.services import ChatService, RoomService
from app.business_logic.unit_of_work import UnitOfWork
from app.domain.events.audit import AuditEvent, Context
from app.domain.events.enums import ActionType
from app.shared.dto.audit import RequestMeta
from app.shared.dto.room import RoomDTO
from app.shared.log_config import LogMixin


class DeleteRoomUseCase(LogMixin):
    """
    Удалить комнату.

    Сценарий:
    - Проверить, что актор это OWNER комнаты.
    - Удалить комнату (чат удалится каскадом).
    - Записать audit-событие.
    """

    def __init__(
        self,
        chat_service: ChatService,
        room_service: RoomService,
        uow: UnitOfWork,
    ):
        self._chat_service = chat_service
        self._room_service = room_service
        self._uow = uow

    async def execute(
        self,
        room_id: UUID,
        actor_id: str,
        request_meta: RequestMeta,
    ) -> RoomDTO:
        time_now = datetime.now(tz=timezone.utc)

        # Проверить права
        owner_id = await self._room_service.get_owner_room(room_id)
        if owner_id != actor_id:
            self.log_warning(
                f"Пользователь {actor_id} пытался удалить комнату {room_id}"
            )
            raise PermissionError(
                f"Пользователь {actor_id} не владелец комнаты {room_id}"
            )

        # Получить данные до обновления
        before = await self._room_service.get(room_id)

        # Удалить комнату
        deleted = await self._room_service.delete(room_id)

        # 4. Audit
        self._uow.add_event(AuditEvent(
            actor_type=ActionType.DELETE_ROOM,
            actor_id=actor_id,
            target_id=str(room_id),
            old_data={
                "title": before.title,
                "max_users": before.max_users,
                "owner_id": owner_id,
            },
            new_data=None,
            context=Context(
                ip=request_meta.ip,
                user_agent=request_meta.user_agent,
                source=request_meta.source,
            ),
            occurred_at=time_now,
        ))

        self.log_info(f"Пользователь {actor_id} удалил комнату {room_id}")
        return deleted