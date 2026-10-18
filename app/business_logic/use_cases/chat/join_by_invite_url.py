from datetime import timezone, datetime
from uuid import UUID
from app.business_logic.exceptions import AlreadyExistsError
from app.business_logic.services import ChatService, RoomService
from app.business_logic.services.invite_token_service import InviteTokenService
from app.business_logic.unit_of_work import UnitOfWork
from app.domain.events.audit import AuditEvent, Context
from app.domain.events.enums import ActionType
from app.shared.dto.audit import RequestMeta
from app.shared.dto.chat import ChatMemberDTO, ChatMemberSaveDTO
from app.shared.dto.enums import ChatRole
from app.shared.log_config import LogMixin


class JoinByInviteUseCase(LogMixin):
    """
    Вступить в комнату по invite-токену.

    Сценарий:
    - Проверить токен.
    - Проверить, что пользователь ещё не в чате.
    - Проверить лимит участников.
    - Добавить участника.
    - Записать audit-событие.
    """

    def __init__(
        self,
        chat_service: ChatService,
        room_service: RoomService,
        invite_service: InviteTokenService,
        uow: UnitOfWork,
    ):
        self._chat_service = chat_service
        self._room_service = room_service
        self._invite_service = invite_service
        self._uow = uow

    async def execute(
        self,
        token: str,
        actor_id: str,
        request_meta: RequestMeta,
    ) -> ChatMemberDTO:
        time_now = datetime.now(tz=timezone.utc)

        # Проверить url токен
        doc = await self._invite_service.validate(token)
        room_id = UUID(doc.room_id)

        # Проверить пользователя в чате
        is_member = await self._chat_service.is_member(room_id, actor_id)
        if is_member:
            raise AlreadyExistsError(
                f"Пользователь {actor_id} уже в чате {room_id}"
            )

        # Проверить олимит участников
        room = await self._room_service.get(room_id)
        members = await self._chat_service.get_members(room_id)
        if len(members) >= room.max_users:
            raise PermissionError(
                f"Комната {room_id} заполнена"
            )

        # Добавить участника в комнату
        member = await self._chat_service.add_member(ChatMemberSaveDTO(
            chat_id=room_id,
            user_id=actor_id,
            role=ChatRole.MEMBER,
        ))

        # Сохранить событие
        self._uow.add_event(AuditEvent(
            actor_type=ActionType.JOIN_BY_INVITE,
            actor_id=actor_id,
            target_id=str(room_id),
            old_data=None,
            new_data={"token": token[:8] + "..."},
            context=Context(
                ip=request_meta.ip,
                user_agent=request_meta.user_agent,
                source=request_meta.source,
            ),
            occurred_at=time_now,
        ))

        self.log_info(f"Пользователь {actor_id} вступил в {room_id} по invite")
        return member