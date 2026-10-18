from datetime import datetime, timezone
from app.business_logic.services import TokenService
from app.business_logic.unit_of_work import UnitOfWork
from app.domain.events.audit import AuditEvent, Context
from app.domain.events.enums import ActionType
from app.shared.dto.audit import RequestMeta
from app.shared.dto.jwt import JWTRefreshTokenResponse
from app.shared.log_config import LogMixin


class LogoutUseCase(LogMixin):
    """
    Выход из системы.

    Сценарий:
    - Отозвать refresh-токен, удалить из white-list.
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
        refresh_token: JWTRefreshTokenResponse,
        request_meta: RequestMeta,
    ) -> None:
        time_now = datetime.now(tz=timezone.utc)

        # Отзыв refresh токена
        await self._token_service.revoke(
            user_id=refresh_token.user_id,
            refresh_id=refresh_token.refresh_id,
        )

        # Сохранение audit события выхода
        self._uow.add_event(AuditEvent(
            actor_type=ActionType.LOGOUT,
            actor_id=refresh_token.user_id,
            target_id=refresh_token.user_id,
            old_data=None,
            new_data=None,
            context=Context(
                ip=request_meta.ip,
                user_agent=request_meta.user_agent,
                source=request_meta.source,
            ),
            occurred_at=time_now,
        ))

        self.log_info(f"Пользователь {refresh_token.user_id} вышел из системы")