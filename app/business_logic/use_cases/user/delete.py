import random
from dataclasses import asdict
from datetime import datetime, timezone
from app.business_logic.exceptions import PermissionError
from app.business_logic.services import ChatService, RoomService, UserService
from app.business_logic.unit_of_work import UnitOfWork
from app.domain.events.audit import AuditEvent, Context
from app.domain.events.enums import ActionType
from app.shared.dto.audit import RequestMeta
from app.shared.dto.enums import ChatRole, RoleEnum
from app.shared.dto.user import UserDtoGet
from app.shared.log_config import LogMixin


class DeleteUserUseCase(LogMixin):
    """
    Удалить пользователя.

    Сценарий:
    - Проверить права актора.
    - Передать владение комнатами (если пользователь — OWNER).
    - Удалить пустые комнаты.
    - Удалить пользователя.
    - Записать audit-событие.
    """

    def __init__(
        self,
        user_service: UserService,
        chat_service: ChatService,
        room_service: RoomService,
        uow: UnitOfWork,
    ):
        self._user_service = user_service
        self._chat_service = chat_service
        self._room_service = room_service
        self._uow = uow

    async def execute(
        self,
        user_id: str,
        actor_id: str,
        request_meta: RequestMeta,
    ) -> UserDtoGet:
        time_now = datetime.now(tz=timezone.utc)

        # Проверка прав для удаления
        actor = await self._user_service.get(actor_id)
        target = await self._user_service.get(user_id)

        if actor_id == user_id:
            self.log_warning(f"Пользователь {actor_id} пытался удалить сам себя")
            raise PermissionError("Нельзя удалить самого себя")

        if not actor.role.can_manage(target.role):
            self.log_warning(f"Пользователь {actor_id} пытался удалить {user_id}")
            raise PermissionError(f"Пользователь {actor_id} не может удалить {user_id}")

        # Получить комнаты, где удаленный пользователь является владельцем
        room_ids, members_by_room = await self._room_service.get_owner_rooms_with_members(user_id)
        for chat_id in room_ids:
            # Сменить владельца
            members = members_by_room.get(chat_id, [])
            new_owner = self._pick_new_owner(members, user_id)

            if new_owner is None:
                # Нет кандидатов — удалить комнату
                await self._room_service.delete(chat_id)
                self.log_info(f"Комната {chat_id} удалена — нет участников")
                continue

            await self._chat_service.transfer_ownership(
                chat_id=chat_id,
                from_user=user_id,
                to_user=new_owner,
            )

        # Удаление пользователя
        deleted = await self._user_service.delete(user_id)

        # Сохранение события в audit
        self._uow.add_event(AuditEvent(
            actor_type=ActionType.DELETE_USER,
            actor_id=actor_id,
            target_id=user_id,
            old_data=asdict(target),
            new_data=None,
            context=Context(
                ip=request_meta.ip,
                user_agent=request_meta.user_agent,
                source=request_meta.source,
            ),
            occurred_at=time_now,
        ))

        self.log_info(f"Пользователь {actor_id} удалил {user_id}")
        return deleted

    @staticmethod
    def _pick_new_owner(
        members: list[tuple[str, ChatRole]],
        leaving_user: str,
    ) -> str | None:
        """
        Выбрать нового владельца.

        Приоритет:
        1. ADMIN (кроме уходящего).
        2. MEMBER (кроме уходящего).
        3. None, если никого.
        """
        admins = [
            uid for uid, role in members
            if role == ChatRole.ADMIN and uid != leaving_user
        ]
        if admins:
            return random.choice(admins)

        members_only = [
            uid for uid, role in members
            if role == ChatRole.MEMBER and uid != leaving_user
        ]
        if members_only:
            return random.choice(members_only)

        return None