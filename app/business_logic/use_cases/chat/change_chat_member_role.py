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

    Сценарий:
    - Проверить, что актор — OWNER.
    - Нельзя менять роль OWNER.
    - Сменить роль.
    - Записать audit-событие.
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

        # Проверить права
        owner_id = await self._room_service.get_owner_room(chat_id)
        if owner_id != actor_id:
            self.log_warning(
                f"Пользователь {actor_id} пытался сменить роль в {chat_id}"
            )
            raise PermissionError(
                f"Пользователь {actor_id} не владелец чата {chat_id}"
            )

        # Нельзя изменить роль у владельца
        if new_role == ChatRole.OWNER:
            raise PermissionError("Нельзя назначить OWNER через смену роли")

        # Получить информацию об участнике
        target = await self._chat_service.get_member(chat_id, user_id)

        # Нельзя изменить роль самому себе
        if actor_id == user_id:
            raise PermissionError("Нельзя менять свою роль")

        if target.role == new_role:
            return target

        # Обновить роль
        updated = await self._chat_service.set_role(chat_id, user_id, new_role)

        # Сохранить событие
        self._uow.add_event(AuditEvent(
            actor_type=ActionType.CHANGE_CHAT_MEMBER_ROLE,
            actor_id=actor_id,
            target_id=user_id,
            old_data={
                "chat_id": str(chat_id),
                "role": target.role.value,
            },
            new_data={
                "chat_id": str(chat_id),
                "role": new_role.value,
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