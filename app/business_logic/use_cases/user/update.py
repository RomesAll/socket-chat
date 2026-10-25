from dataclasses import asdict
from datetime import datetime, timezone
from app.business_logic.services import UserService
from app.business_logic.unit_of_work import UnitOfWork
from app.domain.events.audit import AuditEvent, Context
from app.domain.events.enums import ActionType
from app.shared.dto.audit import RequestMeta
from app.shared.dto.user import UserUpdateDTO, UserDtoGet
from app.shared.log_config import LogMixin
from app.business_logic.exceptions import PermissionError


class UpdateUserUseCase(LogMixin):
    """
    Обновить профиль пользователя.

    Сценарий:
    - Проверить права актора.
    - Получить состояние до (для audit).
    - Обновить пользователя.
    - Записать audit-событие.
    """

    def __init__(
        self,
        user_service: UserService,
        uow: UnitOfWork,
    ):
        self._user_service = user_service
        self._uow = uow

    async def execute(
        self,
        user_id: str,
        dto: UserUpdateDTO,
        actor_id: str,
        request_meta: RequestMeta,
    ) -> UserDtoGet:
        time_now = datetime.now(tz=timezone.utc)

        # Проверка прав для обновления
        actor = await self._user_service.get(actor_id)
        target = await self._user_service.get(user_id)

        if actor_id != user_id and not actor.role.can_manage(target.role):
            self.log_warning(f"Пользователь {actor_id} пытался обновить {user_id}")
            raise PermissionError(f"Пользователь {actor_id} не может обновить {user_id}")

        # Обновить пользователя
        updated = await self._user_service.update(user_id, dto)

        # Сохранить информацию в audit
        self._uow.add_event(AuditEvent(
            actor_type=ActionType.UPDATE_USER,
            actor_id=actor_id,
            target_id=user_id,
            old_data=asdict(target),
            new_data=asdict(updated),
            context=Context(
                ip=request_meta.ip,
                user_agent=request_meta.user_agent,
                source=request_meta.source,
            ),
            occurred_at=time_now,
        ))

        self.log_info(f"Пользователь {actor_id} обновил {user_id}")
        return updated