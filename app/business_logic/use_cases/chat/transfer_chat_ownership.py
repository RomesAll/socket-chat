from datetime import datetime, timezone
from uuid import UUID
from app.business_logic.exceptions import PermissionError
from app.business_logic.services import ChatService, RoomService
from app.business_logic.unit_of_work import UnitOfWork
from app.domain.events.audit import AuditEvent, Context
from app.domain.events.enums import ActionType
from app.shared.dto.audit import RequestMeta
from app.shared.log_config import LogMixin


class TransferChatOwnershipUseCase(LogMixin):
    """
    Передать владение чатом.

    Сценарий:
    - Проверить, что актор — OWNER.
    - Проверить, что целевой — участник.
    - Передать владение (OWNER → ADMIN, target → OWNER).
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
        chat_id: UUID,
        to_user: str,
        actor_id: str,
        request_meta: RequestMeta,
    ) -> None:
        time_now = datetime.now(tz=timezone.utc)

        # Проверить права
        owner_id = await self._room_service.get_owner_room(chat_id)
        if owner_id != actor_id:
            self.log_warning(
                f"Пользователь {actor_id} пытался передать владение {chat_id}"
            )
            raise PermissionError(
                f"Пользователь {actor_id} не владелец чата {chat_id}"
            )

        # Нельзя перопределить владельца на себя
        if actor_id == to_user:
            raise PermissionError("Нельзя передать владение себе")

        # Проверить, является ли новый пользователь участником
        target = await self._chat_service.get_member(chat_id, to_user)

        # Передать права
        await self._chat_service.transfer_ownership(
            chat_id=chat_id,
            from_user=actor_id,
            to_user=to_user,
        )

        # Сохранить событие
        self._uow.add_event(AuditEvent(
            actor_type=ActionType.TRANSFER_CHAT_OWNERSHIP,
            actor_id=actor_id,
            target_id=to_user,
            old_data={"owner_id": actor_id},
            new_data={"owner_id": to_user},
            context=Context(
                ip=request_meta.ip,
                user_agent=request_meta.user_agent,
                source=request_meta.source,
            ),
            occurred_at=time_now,
        ))

        self.log_info(
            f"В чате {chat_id} владелец сменился с {actor_id} на {to_user}"
        )