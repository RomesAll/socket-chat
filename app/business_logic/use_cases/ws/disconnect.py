from datetime import datetime, timezone
from uuid import UUID
from app.business_logic.services import ChatService
from app.infrastructure.redis import PresenceCache, SessionKeyStorage
from app.infrastructure.websocket import UserConnectionManager, WSBroker
from app.shared.dto.audit import RequestMeta
from app.shared.log_config import LogMixin


class DisconnectWebSocketUseCase(LogMixin):
    """
    Отключить WebSocket-сессию пользователя.

    Сценарий:
    - Отписать от всех чатов (через WSBroker).
    - Удалить session_key.
    - Удалить подключение.
    - Сбросить online (если больше нет сессий).
    - Записать audit.
    """

    def __init__(
        self,
        chat_service: ChatService,
        session_storage: SessionKeyStorage,
        manager: UserConnectionManager,
        ws_broker: WSBroker,
        presence: PresenceCache,
    ):
        self._chat_service = chat_service
        self._session_storage = session_storage
        self._manager = manager
        self._ws_broker = ws_broker
        self._presence = presence

    async def execute(
        self,
        ws,
        user_id: str,
        session_id: UUID,
        request_meta: RequestMeta,
    ) -> None:
        time_now = datetime.now(tz=timezone.utc)

        # Отписаться от чатов
        chats = await self._chat_service.get_chats_user(user_id)
        for chat in chats:
            await self._ws_broker.publish_leave_chat(
                action_type="leave_chat",
                chat_id=chat.id,
                user_id=user_id,
            )

        # Удалить session_key
        await self._session_storage.delete(user_id, session_id)

        # Удалить подключение
        await self._manager.disconnect(ws)

        if not self._manager.is_online(user_id):
            await self._presence.set_offline(user_id)

        self.log_info(f"Пользователь {user_id} отключился (session={session_id})")