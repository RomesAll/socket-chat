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

        # Проверить права
        is_self = actor_id == user_id
        is_admin = await self._chat_service.is_admin(chat_id, actor_id)

        if not is_self and not is_admin:
            raise PermissionError(f"Пользователь {actor_id} не админ чата {chat_id}")

        # Получить информацию об участнике
        target = await self._chat_service.get_member(chat_id, user_id)

        # Логика для OWNER
        if target.role == ChatRole.OWNER:
            if not is_self:
                raise PermissionError("Нельзя удалить владельца чата")

            # Если владелец выходит сам — передаем права
            new_owner = await self._chat_service.transfer_ownership_on_leave(chat_id, user_id)

            if not new_owner:
                # Если больше никого нет — удаляем чат полностью
                await self._chat_service.delete(chat_id)
                return target

        # Запрет на удаление другого админа
        if target.role == ChatRole.ADMIN and not is_self:
            raise PermissionError("Нельзя удалить другого админа")

        # Удаление пользователя из чата
        removed = await self._chat_service.remove_member(chat_id, user_id)

        self._uow.add_after_commit(
            lambda: self._ws_broker.publish_to_user(
                action_type="kicked_from_chat",
                user_id=user_id,
                data={"chat_id": str(chat_id)}
            )
        )

        # Отправляем в сам чат, чтобы у остальных обновился список участников (если открыта модалка)
        self._uow.add_after_commit(
            lambda: self._ws_broker.publish_to_chat(
                action_type="member_removed",
                chat_id=chat_id,
                data={"user_id": user_id}
            )
        )

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

        self.log_info(f"Пользователь {actor_id} удалил {user_id} из чата {chat_id}")
        return removed