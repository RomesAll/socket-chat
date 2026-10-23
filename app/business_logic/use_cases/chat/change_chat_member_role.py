from datetime import datetime, timezone
from uuid import UUID
from app.business_logic.exceptions import PermissionError
from app.business_logic.services import RoomService, ChatService
from app.business_logic.unit_of_work import UnitOfWork
from app.domain.events.audit import AuditEvent, Context
from app.domain.events.enums import ActionType
from app.shared.dto.audit import RequestMeta
from app.shared.dto.chat import ChatMemberDTO
from app.shared.dto.enums import ChatRole
from app.shared.log_config import LogMixin


class ChangeChatMemberRoleUseCase(LogMixin):
    """
    Сменить роль участника чата.
    """

    def __init__(
        self,
        room_service: RoomService,
        chat_service: ChatService,
        uow: UnitOfWork,
    ):
        self._room_service = room_service
        self._chat_service = chat_service
        self._uow = uow

    async def execute(
        self,
        chat_id: UUID,
        user_id: str,
        new_role: ChatRole,
        actor_id: str,
        request_meta: RequestMeta,
    ) -> ChatMemberDTO:
        time_now = datetime.now(tz=timezone.utc)

        # Нельзя изменить свою роль
        if actor_id == user_id:
            raise PermissionError("Нельзя менять свою роль")

        # Получить участников
        actor = await self._chat_service.get_member(chat_id, actor_id)
        target = await self._chat_service.get_member(chat_id, user_id)

        # Проверка прав: актор должен иметь право управлять ролью цели
        if not actor.role.can_manage(target.role):
            raise PermissionError(f"Пользователь {actor_id} не может изменить роль {user_id}")

        # Если роль не меняется — ничего не делаем
        if target.role == new_role:
            return target

        if new_role == ChatRole.OWNER:
            await self._chat_service.set_role(chat_id, actor_id, ChatRole.ADMIN)

        # Обновить роль в БД
        updated = await self._chat_service.set_role(chat_id, user_id, new_role)

        # Сохранить событие
        self._uow.add_event(AuditEvent(
            actor_type=ActionType.CHANGE_CHAT_MEMBER_ROLE,
            actor_id=actor_id,
            target_id=user_id,
            old_data={
                "chat_id": str(chat_id),
                "role": target.role.value if hasattr(target.role, 'value') else target.role,
            },
            new_data={
                "chat_id": str(chat_id),
                "role": new_role.value if hasattr(new_role, 'value') else new_role,
            },
            context=Context(
                ip=request_meta.ip,
                user_agent=request_meta.user_agent,
                source=request_meta.source,
            ),
            occurred_at=time_now,
        ))

        self.log_info(f"Пользователь {actor_id} сменил роль {user_id} в {chat_id}")
        return updated