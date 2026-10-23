from datetime import datetime, timezone
from uuid import UUID
from app.business_logic.services import ChatService
from app.business_logic.services.invite_token_service import InviteTokenService
from app.business_logic.unit_of_work import UnitOfWork
from app.domain.events.audit import AuditEvent, Context
from app.domain.events.enums import ActionType
from app.shared.dto.audit import RequestMeta
from app.shared.log_config import LogMixin


class GenerateInviteLinkUseCase(LogMixin):
    """
    Сгенерировать invite-ссылку для вступления в комнату.

    Сценарий:
    - Проверить, что актор — админ комнаты.
    - Сгенерировать токен.
    - Записать audit-событие.
    - Вернуть URL.
    """

    def __init__(
        self,
        chat_service: ChatService,
        invite_service: InviteTokenService,
        uow: UnitOfWork,
    ):
        self._chat_service = chat_service
        self._invite_service = invite_service
        self._uow = uow

    async def execute(
        self,
        room_id: UUID,
        hours: int,
        max_uses: int | None,
        actor_id: str,
        request_meta: RequestMeta,
    ) -> str:
        time_now = datetime.now(tz=timezone.utc)

        # Проверка прав доступа
        is_owner = await self._chat_service.is_owner(room_id, actor_id)
        if not is_owner:
            raise PermissionError(
                f"Пользователь {actor_id} не владелец комнаты {room_id}"
            )

        # Генерация и сохранения url токена
        token = await self._invite_service.generate(
            room_id=room_id,
            created_by=actor_id,
            hours=hours,
            max_uses=max_uses,
        )

        # Сохранить событие генерации токена
        self._uow.add_event(AuditEvent(
            actor_type=ActionType.GENERATE_INVITE_LINK,
            actor_id=actor_id,
            target_id=str(room_id),
            old_data=None,
            new_data={
                "hours": hours,
                "max_uses": max_uses,
            },
            context=Context(
                ip=request_meta.ip,
                user_agent=request_meta.user_agent,
                source=request_meta.source,
            ),
            occurred_at=time_now,
        ))

        return token