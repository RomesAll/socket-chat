from app.business_logic.exceptions import AuthError
from app.business_logic.unit_of_work import UnitOfWork
from app.domain.events.enums import ActionType
from app.shared.dto.audit import RequestMeta
from app.shared.dto.auth import LoginDtoRequest, LoginOrRegisterDtoResponse
from app.shared.dto.enums import SendType
from app.shared.log_config import LogMixin
from app.business_logic.services import UserService, VerificationService
from app.infrastructure.email import EmailSender
from app.domain.events.audit import AuditEvent, Context
from datetime import datetime, timezone


class LoginWithSendCodeUseCase(LogMixin):
    """
    Аутентификация пользователя по ID пользователя и паролю
    с отправкой кода подтверждения по email.

    Сценарий:
    - Найти пользователя по ID.
    - Проверить хеши паролей.
    - Сгенерировать и сохранить код подтверждения в Redis.
    - Сохранить код в Redis.
    - Записать audit событие.
    - Отправить код пользователю по email.
    """

    def __init__(
            self,
            user_service: UserService,
            email_sender: EmailSender,
            verification_service: VerificationService,
            uow: UnitOfWork
    ):
        self._user_service = user_service
        self._verification_service = verification_service
        self._uow = uow
        self._email_sender = email_sender

    async def execute(
            self,
            cred: LoginDtoRequest,
            request_meta: RequestMeta
    ) -> LoginOrRegisterDtoResponse:
        time_now = datetime.now(tz=timezone.utc)

        # Получить информацию о пользователе, если нет, то исключение RecordNotFound
        user_info = await self._user_service.get(cred.user_id)

        # Проверить хеши паролей
        is_success = await self._user_service.verify_password(
            user_id=cred.user_id,
            password=cred.password
        )
        if not is_success:
            # Если хеши не равны, то audit событие AUTH_FAILED
            self._uow.add_event(AuditEvent(
                actor_type=ActionType.AUTH_FAILED,
                actor_id=cred.user_id,
                target_id=cred.user_id,
                old_data=None,
                new_data=None,
                context=Context(
                    ip=request_meta.ip,
                    user_agent=request_meta.user_agent,
                    source=request_meta.source
                ),
                occurred_at=time_now
            ))
            self.log_warning(f"Неудачная попытка входа: user_id={cred.user_id}")
            raise AuthError()

        # Генерация и сохранение кода подтверждения в redis
        code = await self._verification_service.generate_and_save(cred.user_id)

        # Сохранение audit события SEND_VERIFY_CODE
        self._uow.add_event(AuditEvent(
            actor_type=ActionType.SEND_VERIFY_CODE,
            actor_id=cred.user_id,
            target_id=cred.user_id,
            old_data=None,
            new_data=None,
            context=Context(
                ip=request_meta.ip,
                user_agent=request_meta.user_agent,
                source=request_meta.source
            ),
            occurred_at=time_now
        ))

        # Добавление отложенного действия после комита для отправки кода по email
        self._uow.add_after_commit(
            lambda: self._email_sender.send_accept_code(user_info.email, str(code))
        )

        self.log_info(f"Код отправлен пользователю {cred.user_id}")
        return LoginOrRegisterDtoResponse(
            send_code=SendType.EMAIL,
            time_send=time_now
        )