from datetime import datetime, timezone
from uuid import UUID, uuid4

from app.business_logic.services import ChatService, UserService
from app.domain.events.audit import AuditEvent, Context
from app.domain.events.enums import ActionType
from app.infrastructure.redis import PresenceCache, SessionKeyStorage
from app.infrastructure.websocket import UserConnectionManager, WSBroker
from app.shared.dto.audit import RequestMeta
from app.shared.log_config import LogMixin


class ConnectWebSocketUseCase(LogMixin):
    """
    Подключить WebSocket-сессию пользователя.

    Сценарий:
    - Проверить, что пользователь существует.
    - Сохранить session_key в Redis.
    - Зарегистрировать подключение.
    - Установить online-статус.
    - Подписать на все чаты пользователя (через WSBroker).
    - Записать audit.
    """

    def __init__(
        self,
        user_service: UserService,
        chat_service: ChatService,
        session_storage: SessionKeyStorage,
        manager: UserConnectionManager,
        ws_broker: WSBroker,
        presence: PresenceCache,
    ):
        self._user_service = user_service
        self._chat_service = chat_service
        self._session_storage = session_storage
        self._manager = manager
        self._ws_broker = ws_broker
        self._presence = presence

    async def execute(
        self,
        ws,
        user_id: str,
        session_key: bytes,
        request_meta: RequestMeta,
    ) -> UUID:
        time_now = datetime.now(tz=timezone.utc)

        # Проверка пользователя
        await self._user_service.get(user_id)

        # Генерация id сессии
        session_id = uuid4()
        await self._session_storage.save(user_id, session_id, session_key)

        # Регистрация подключения
        await self._manager.connection(ws, user_id, session_id)

        # Установить статус пользователя
        await self._presence.set_online(user_id)

        # Подписать на все чаты пользователя
        chats = await self._chat_service.get_chats_user(user_id)
        for chat in chats:
            await self._ws_broker.publish_join_chat(
                action_type="join_chat",
                chat_id=chat.id,
                user_id=user_id,
            )

        self.log_info(f"Пользователь {user_id} подключился (session={session_id})")
        return session_id