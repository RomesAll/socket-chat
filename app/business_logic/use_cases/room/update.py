from datetime import datetime, timezone
from uuid import UUID
from app.business_logic.exceptions import PermissionError
from app.business_logic.services import ChatService, RoomService
from app.business_logic.unit_of_work import UnitOfWork
from app.domain.events.audit import AuditEvent, Context
from app.domain.events.enums import ActionType
from app.shared.dto.audit import RequestMeta
from app.shared.dto.room import RoomUpdateDTO, RoomDTO
from app.shared.log_config import LogMixin


class UpdateRoomUseCase(LogMixin):
    """
    Обновить метаданные комнаты.

    Сценарий:
    - Проверить, что актор — ADMIN или OWNER комнаты.
    - Получить состояние до (для audit).
    - Обновить комнату.
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
        dto: RoomUpdateDTO,
        actor_id: str,
        request_meta: RequestMeta,
    ) -> RoomDTO:
        time_now = datetime.now(tz=timezone.utc)

        # Права: OWNER или ADMIN комнаты
        is_admin = await self._chat_service.is_admin(room_id, actor_id)
        if not is_admin:
            self.log_warning(
                f"Пользователь {actor_id} пытался обновить комнату {room_id}"
            )
            raise PermissionError(
                f"Пользователь {actor_id} не админ комнаты {room_id}"
            )

        # Состояние до
        before = await self._room_service.get(room_id)

        # Обновить
        updated = await self._room_service.update(room_id, dto)

        # Audit — только изменённые поля
        old_data, new_data = self._diff(before, updated)

        self._uow.add_event(AuditEvent(
            actor_type=ActionType.UPDATE_ROOM,
            actor_id=actor_id,
            target_id=str(room_id),
            old_data=old_data or None,
            new_data=new_data or None,
            context=Context(
                ip=request_meta.ip,
                user_agent=request_meta.user_agent,
                source=request_meta.source,
            ),
            occurred_at=time_now,
        ))

        self.log_info(f"Пользователь {actor_id} обновил комнату {room_id}")
        return updated

    @staticmethod
    def _diff(before, after) -> tuple[dict, dict]:
        """Только изменённые поля."""
        old, new = {}, {}
        for f in ("title", "max_users", "description", "avatar_url"):
            b = getattr(before, f, None)
            a = getattr(after, f, None)
            if b != a:
                old[f] = b
                new[f] = a
        return old, new