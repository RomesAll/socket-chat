from datetime import datetime, timezone
from app.business_logic.exceptions import VerifyCodeInCorrect
from app.business_logic.services import UserService, VerificationService, TokenService
from app.business_logic.unit_of_work import UnitOfWork
from app.domain.events.audit import AuditEvent, Context
from app.domain.events.enums import ActionType
from app.shared.dto.audit import RequestMeta
from app.shared.dto.auth import VerifyCodeRequest
from app.shared.dto.jwt import JWTTokenResponse
from app.shared.log_config import LogMixin


class VerifyCodeUseCase(LogMixin):
    """
    Подтверждение кода и выдача пары access и refresh токенов.

    Сценарий:
    - Проверить код подтверждения.
    - Создать пару access и refresh токенов.
    - Записать refresh_id в white list.
    - Записать audit-событие.
    - Вернуть токены.
    """

    def __init__(
        self,
        user_service: UserService,
        verification_service: VerificationService,
        token_service: TokenService,
        uow: UnitOfWork,
    ):
        self._user_service = user_service
        self._verification_service = verification_service
        self._token_service = token_service
        self._uow = uow

    async def execute(
        self,
        request: VerifyCodeRequest,
        request_meta: RequestMeta,
    ) -> JWTTokenResponse:
        time_now = datetime.now(tz=timezone.utc)

        # Получить информацию о пользователе, если нет, то исключение RecordNotFound
        user = await self._user_service.get(request.user_id)

        # Проверить код
        is_valid = await self._verification_service.validate(
            user_id=request.user_id,
            code=request.code,
        )
        if not is_valid:
            self.log_warning(
                f"Неверный код подтверждения: user_id={request.user_id}"
            )
            self._uow.add_event(AuditEvent(
                actor_type=ActionType.VERIFY_CODE_FAILED,
                actor_id=request.user_id,
                target_id=request.user_id,
                old_data=None,
                new_data=None,
                context=Context(
                    ip=request_meta.ip,
                    user_agent=request_meta.user_agent,
                    source=request_meta.source,
                ),
                occurred_at=time_now,
            ))
            raise VerifyCodeInCorrect()

        # Создать пару токенов
        tokens = await self._token_service.create_jwt_auth_tokens(
            user_id=user.id,
            sub=user.display_name,
            role=user.role,
        )

        # Сохранить audit события успешной проверки кода
        self._uow.add_event(AuditEvent(
            actor_type=ActionType.VERIFY_CODE,
            actor_id=request.user_id,
            target_id=request.user_id,
            old_data=None,
            new_data=None,
            context=Context(
                ip=request_meta.ip,
                user_agent=request_meta.user_agent,
                source=request_meta.source,
            ),
            occurred_at=time_now,
        ))

        self.log_info(f"Пользователь {request.user_id} подтвердил код")
        return tokens