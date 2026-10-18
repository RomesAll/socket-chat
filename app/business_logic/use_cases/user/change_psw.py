from datetime import datetime, timezone
from uuid import UUID
from app.business_logic.exceptions import AuthError, PermissionError
from app.business_logic.services import TokenService, UserService
from app.business_logic.unit_of_work import UnitOfWork
from app.domain.events.audit import AuditEvent, Context
from app.domain.events.enums import ActionType
from app.shared.dto.audit import RequestMeta
from app.shared.dto.enums import RoleEnum
from app.shared.dto.user import UserDtoGet
from app.shared.log_config import LogMixin


class ChangeUserPasswordUseCase(LogMixin):
    """
    Сменить пароль пользователя.

    Сценарий:
    - Проверить права (сам или админ).
    - Если сам — проверить старый пароль.
    - Сменить пароль.
    - Отозвать все refresh-токены (кроме текущего).
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
        current_refresh_id: UUID | None = None,
    ) -> UserDtoGet:
        time_now = datetime.now(tz=timezone.utc)

        # Проверка прав для смены пароля
        actor = await self._user_service.get(actor_id)
        is_self = actor_id == user_id
        is_admin = actor.role in (RoleEnum.ADMIN, RoleEnum.SUPER_ADMIN)

        if not is_self and not is_admin:
            self.log_warning(
                f"Пользователь {actor_id} пытался сменить пароль {user_id}"
            )
            raise PermissionError(
                f"Пользователь {actor_id} не может сменить пароль {user_id}"
            )

        # Если пользователь сам меняет пароль, то проверить
        if is_self:
            if not old_password:
                raise AuthError()

            is_correct = await self._user_service.verify_password(
                user_id=user_id,
                password=old_password,
            )
            if not is_correct:
                self.log_warning(
                    f"Неверный старый пароль: user_id={user_id}"
                )
                self._uow.add_event(AuditEvent(
                    actor_type=ActionType.CHANGE_PASSWORD_FAILED,
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
                raise AuthError()

        # Обновить парооль пользователя
        updated = await self._user_service.update_password(user_id, new_password)

        # Отозвать все refresh-токены, кроме текущего
        exclude_id_token = {current_refresh_id, } if current_refresh_id else None
        await self._token_service.revoke_all(
            user_id=user_id,
            exclude_token_ids=exclude_id_token
        )

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

        self.log_info(
            f"Пользователь {actor_id} сменил пароль {user_id}"
        )

        return updated