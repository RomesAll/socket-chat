from datetime import datetime, timezone
from uuid import UUID
from app.business_logic.exceptions import PermissionError
from app.business_logic.services import ChatService
from app.business_logic.unit_of_work import UnitOfWork
from app.domain.events.audit import AuditEvent, Context
from app.domain.events.enums import ActionType
from app.infrastructure.websocket import WSBroker
from app.shared.dto.audit import RequestMeta
from app.shared.dto.chat import ChatMemberDTO
from app.shared.dto.enums import ChatRole
from app.shared.log_config import LogMixin


class RemoveChatMemberUseCase(LogMixin):
    def __init__(
            self,
            chat_service: ChatService,
            ws_broker: WSBroker,
            uow: UnitOfWork,
    ):
        self._chat_service = chat_service
        self._uow = uow
        self._ws_broker = ws_broker

    async def execute(
            self,
            chat_id: UUID,
            user_id: str,
            actor_id: str,
            request_meta: RequestMeta,
    ) -> ChatMemberDTO:
        time_now = datetime.now(tz=timezone.utc)
        is_self = actor_id == user_id

        # Получить информацию об акторе и target
        actor = await self._chat_service.get_member(chat_id, actor_id)
        target = await self._chat_service.get_member(chat_id, user_id)

        # Проверить права
        if not is_self and not actor.role.can_manage(target.role):
            raise PermissionError(f"Пользователь {actor_id} не может удалить {user_id}")

        chat_deleted = False
        if target.role == ChatRole.OWNER:
            # Процесс смены владельца
            new_owner = await self._chat_service.transfer_ownership_on_leave(chat_id, user_id)

            if not new_owner:
                # Если больше никого нет — удаляем чат полностью
                await self._chat_service.delete(chat_id)
                chat_deleted = True

        if not chat_deleted:
            removed = await self._chat_service.remove_member(chat_id, user_id)
        else:
            removed = target

        if chat_deleted:
            self._uow.add_after_commit(
                lambda: self._ws_broker.publish_to_user(
                    action_type="chat_deleted",
                    user_id=user_id,
                    data={"chat_id": str(chat_id)}
                )
            )
            self.log_info(f"Владелец {actor_id} покинул чат {chat_id}. Чат полностью удален.")
        else:
            self._uow.add_after_commit(
                lambda: self._ws_broker.publish_to_user(
                    action_type="kicked_from_chat",
                    user_id=user_id,
                    data={"chat_id": str(chat_id)}
                )
            )
            self._uow.add_after_commit(
                lambda: self._ws_broker.publish_to_chat(
                    action_type="member_removed",
                    chat_id=chat_id,
                    data={"user_id": user_id}
                )
            )
            action = "вышел из чата" if is_self else f"удалил {user_id} из чата"
            self.log_info(f"Пользователь {actor_id} {action} {chat_id}")

        # Сохранить событие
        self._uow.add_event(AuditEvent(
            actor_type=ActionType.REMOVE_CHAT_MEMBER,
            actor_id=actor_id,
            target_id=user_id,
            old_data={"chat_id": str(chat_id), "role": target.role.value},
            new_data=None,
            context=Context(
                ip=request_meta.ip,
                user_agent=request_meta.user_agent,
                source=request_meta.source,
            ),
            occurred_at=time_now,
        ))
        return removed