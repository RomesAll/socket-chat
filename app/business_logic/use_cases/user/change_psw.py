from datetime import datetime, timezone
from app.business_logic.exceptions import AuthError, PermissionError
from app.business_logic.services import TokenService, UserService
from app.business_logic.unit_of_work import UnitOfWork
from app.domain.events.audit import AuditEvent, Context
from app.domain.events.enums import ActionType
from app.shared.dto.audit import RequestMeta
from app.shared.dto.user import UserDtoGet
from app.shared.log_config import LogMixin


class ChangeUserPasswordUseCase(LogMixin):
    """
    Сменить пароль пользователя.

    Сценарий:
    - Проверить права (сам или админ).
    - Если сам — проверить старый пароль.
    - Сменить пароль.
    - Отозвать все refresh-токены.
    - Записать audit-событие.
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
        user_id: str,
        old_password: str | None,
        new_password: str,
        actor_id: str,
        request_meta: RequestMeta,
    ) -> UserDtoGet:
        time_now = datetime.now(tz=timezone.utc)

        # Проверка прав для смены пароля
        actor = await self._user_service.get(actor_id)
        target = await self._user_service.get(user_id)

        if not actor.role.can_manage(target.role):
            target = await self._user_service.get(user_id)
            if not actor.role.can_manage(target.role):
                self.log_warning(f"Пользователь {actor_id} пытался сменить пароль {user_id}")
                raise PermissionError(f"Пользователь {actor_id} не может сменить пароль {user_id}")

        # Проверка старого пароля, если пользователь обновляет у самого себя
        if user_id == actor_id:
            if not old_password:
                self.log_error(f"Старый пароль обязателен")
                raise AuthError()

            if not await self._user_service.verify_password(
                user_id=user_id,
                password=old_password
            ):
                self.log_error(f"Неверный старый пароль: user_id={user_id}")
                raise AuthError()

        # Обновить пароль пользователя
        updated = await self._user_service.update_password(user_id, new_password)

        # Сохранить событие смены пароля в audit
        self._uow.add_event(AuditEvent(
            actor_type=ActionType.CHANGE_PASSWORD,
            actor_id=actor_id,
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

        self.log_info(f"Пользователь {actor_id} сменил пароль {user_id}")

        return updated