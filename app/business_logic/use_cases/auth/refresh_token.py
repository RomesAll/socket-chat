from datetime import datetime, timezone
from app.business_logic.exceptions import RefreshTokenInActive
from app.business_logic.services import UserService, TokenService
from app.business_logic.unit_of_work import UnitOfWork
from app.domain.events.audit import AuditEvent, Context
from app.domain.events.enums import ActionType
from app.shared.dto.audit import RequestMeta
from app.shared.dto.jwt import JWTRefreshTokenResponse, JWTTokenResponse
from app.shared.log_config import LogMixin


class RefreshTokenUseCase(LogMixin):
    """
    Обновить пару access и refresh токенов по refresh-токену.

    Сценарий:
    - Проверить существования пользователя.
    - Проверить, что refresh активен и не отозван.
    - Создать новую пару токенов.
    - Записать audit-событие.
    - Вернуть новые токены.
    """

    def __init__(
        self,
        user_service: UserService,
        token_service: TokenService,
        uow: UnitOfWork,
    ):
        self._user_service = user_service
        self._token_service = token_service
        self._uow = uow

    async def execute(
        self,
        refresh_token: JWTRefreshTokenResponse,
        request_meta: RequestMeta,
    ) -> JWTTokenResponse:
        time_now = datetime.now(tz=timezone.utc)

        # Получить информацию о пользователе, если нет, то исключение RecordNotFound
        user_info = await self._user_service.get(refresh_token.user_id)

        # Проверка активности refresh токена
        is_active = await self._token_service.is_active(
            user_id=refresh_token.user_id,
            refresh_id=refresh_token.refresh_id,
        )
        if not is_active:
            self.log_warning(
                f"Попытка использовать неактивный refresh токен: "
                f"user_id={refresh_token.user_id}, "
                f"refresh_id={refresh_token.refresh_id}"
            )
            self._uow.add_event(AuditEvent(
                actor_type=ActionType.REFRESH_FAILED,
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
            raise RefreshTokenInActive(
                refresh_token.user_id,
                refresh_token.refresh_id,
            )

        # Создать новую пару
        tokens = await self._token_service.refresh_jwt_auth_tokens(
            refresh_token=refresh_token,
        )

        # Сохранить audit события обновления токена
        self._uow.add_event(AuditEvent(
            actor_type=ActionType.REFRESH,
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

        self.log_info(f"Обновлены токены для {refresh_token.user_id}")
        return tokens