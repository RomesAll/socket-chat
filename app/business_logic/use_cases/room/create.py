from datetime import datetime, timezone
from uuid import uuid4
from app.business_logic.services import ChatService, RoomService
from app.business_logic.unit_of_work import UnitOfWork
from app.domain.events.audit import AuditEvent, Context
from app.domain.events.enums import ActionType
from app.infrastructure.websocket import WSBroker
from app.shared.dto.audit import RequestMeta
from app.shared.dto.chat import ChatMemberSaveDTO, ChatSaveDTO
from app.shared.dto.enums import ChatRole, ChatType
from app.shared.dto.room import RoomSaveDTO, RoomDetailsDTO
from app.shared.log_config import LogMixin


class CreateRoomUseCase(LogMixin):
    """
    Создать комнату.

    Сценарий:
    - Создать чат.
    - Создать комнату.
    - Добавить создателя как OWNER.
    - Записать audit-событие.
    """

    def __init__(
        self,
        chat_service: ChatService,
        room_service: RoomService,
        uow: UnitOfWork,
        ws_broker: WSBroker
    ):
        self._chat_service = chat_service
        self._room_service = room_service
        self._uow = uow
        self._ws_broker = ws_broker

    async def execute(
        self,
        title: str,
        description: str | None,
        max_users: int,
        actor_id: str,
        request_meta: RequestMeta,
    ) -> RoomDetailsDTO:
        time_now = datetime.now(tz=timezone.utc)
        chat_id = uuid4()

        # Добавить чат
        chat = await self._chat_service.save(ChatSaveDTO(
            id=chat_id,
            type=ChatType.ROOM,
        ))

        # Добавить комнату
        room = await self._room_service.save(RoomSaveDTO(
            chat_id=chat.id,
            title=title,
            description=description,
            max_users=max_users,
        ))

        # Добавить создателя с ролью OWNER
        await self._chat_service.add_member(ChatMemberSaveDTO(
            chat_id=chat.id,
            user_id=actor_id,
            role=ChatRole.OWNER,
        ))

        self._uow.add_after_commit(
            lambda: self._ws_broker.publish_join_chat(
                action_type="join_chat",
                chat_id=chat.id,
                user_id=actor_id
            )
        )

        # Сохранить события создания комнаты
        self._uow.add_event(AuditEvent(
            actor_type=ActionType.CRETE_NEW_ROOM,
            actor_id=actor_id,
            target_id=str(chat.id),
            old_data=None,
            new_data={
                "title": title,
                "max_users": max_users,
            },
            context=Context(
                ip=request_meta.ip,
                user_agent=request_meta.user_agent,
                source=request_meta.source,
            ),
            occurred_at=time_now,
        ))

        self.log_info(f"Пользователь {actor_id} создал комнату {chat.id}")

        return RoomDetailsDTO(
            chat_id=chat.id,
            title=room.title,
            max_users=room.max_users,
            description=room.description,
            avatar_url=room.avatar_url,
            owner_id=actor_id,
            members_count=1,
            admins_count=0,
            created_at=room.created_at,
            updated_at=room.updated_at,
        )