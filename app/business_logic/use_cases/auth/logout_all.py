from datetime import datetime, timezone
from app.business_logic.services import TokenService
from app.business_logic.unit_of_work import UnitOfWork
from app.domain.events.audit import AuditEvent, Context
from app.domain.events.enums import ActionType
from app.shared.dto.audit import RequestMeta
from app.shared.log_config import LogMixin


class LogoutAllUseCase(LogMixin):
    """
    Выход со всех устройств.

    Сценарий:
    - Отозвать все refresh-токены пользователя.
    - Закрыть все WebSocket-подключения.
    - Записать audit-событие.
    """

    def __init__(
        self,
        token_service: TokenService,
        uow: UnitOfWork,
    ):
        self._token_service = token_service
        self._uow = uow

    async def execute(
        self,
        user_id: str,
        request_meta: RequestMeta,
    ) -> None:
        time_now = datetime.now(tz=timezone.utc)

        # Отозвать все refresh-токены
        await self._token_service.revoke_all(user_id)

        # Сохранить audit событие выхода
        self._uow.add_event(AuditEvent(
            actor_type=ActionType.LOGOUT_ALL,
            actor_id=user_id,
            target_id=user_id,
            old_data=None,
            new_data=None,
            context=Context(
                ip=request_meta.ip,
                user_agent=request_meta.user_agent,
                source=request_meta.source,
            ),
            occurred_at=time_now,
        ))

        self.log_info(f"Пользователь {user_id} вышел со всех устройств")