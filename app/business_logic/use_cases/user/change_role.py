from datetime import datetime, timezone
from uuid import UUID

from app.business_logic.exceptions import PermissionError
from app.business_logic.services import UserService, TokenService
from app.business_logic.unit_of_work import UnitOfWork
from app.domain.events.audit import AuditEvent, Context
from app.domain.events.enums import ActionType
from app.shared.dto.audit import RequestMeta
from app.shared.dto.enums import RoleEnum
from app.shared.dto.user import UserDtoGet
from app.shared.log_config import LogMixin


class ChangeUserRoleUseCase(LogMixin):
    """
    Сменить роль пользователя.

    Сценарий:
    - Проверить, что актор это админ.
    - Получить состояние до для audit.
    - Сменить роль.
    - Записать audit-событие.
    """

    def __init__(
        self,
        user_service: UserService,
        token_service: TokenService,
        uow: UnitOfWork,
    ):
        self._user_service = user_service
        self._uow = uow
        self._token_service = token_service

    async def execute(
        self,
        user_id: str,
        new_role: RoleEnum,
        actor_id: str,
        request_meta: RequestMeta,
    ) -> UserDtoGet:
        time_now = datetime.now(tz=timezone.utc)

        # Нельзя изменить свою роль самостоятельно!
        if actor_id == user_id:
            self.log_warning(f"Пользователь {actor_id} пытался сменить свою роль")
            raise PermissionError("Нельзя менять свою роль")

        # Проверка роли актора
        actor = await self._user_service.get(actor_id)
        target = await self._user_service.get(user_id)

        if not actor.role.can_manage(target.role):
            self.log_warning(f"Пользователь {actor_id} пытался сменить роль {user_id}")
            raise PermissionError(f"Пользователь {actor_id} не может изменить роль {user_id}")

        if actor.role == RoleEnum.ADMIN and new_role > actor.role:
            self.log_warning(f"Админ {actor_id} не может создать роль выше своей {user_id}")
            raise PermissionError(f"Админ {actor_id} не может создать роль выше своей {user_id}")

        # Если роль та же
        if target.role == new_role:
            self.log_info(f"Роль пользователя {user_id} уже {new_role}")
            return target

        # Сменить роль пользователя
        updated = await self._user_service.update_role(user_id, new_role)

        # Сохранение в audit
        self._uow.add_event(AuditEvent(
            actor_type=ActionType.CHANGE_USER_ROLE,
            actor_id=actor_id,
            target_id=user_id,
            old_data={"role": target.role.value},
            new_data={"role": new_role.value},
            context=Context(
                ip=request_meta.ip,
                user_agent=request_meta.user_agent,
                source=request_meta.source,
            ),
            occurred_at=time_now,
        ))

        self.log_info(
            f"Пользователь {actor_id} сменил роль {user_id}: "
            f"{target.role} → {new_role}"
        )

        return updated