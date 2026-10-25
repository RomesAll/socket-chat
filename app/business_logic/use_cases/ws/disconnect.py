from uuid import UUID
from app.business_logic.services import ChatService, UserService
from app.infrastructure.redis import PresenceCache, SessionKeyStorage
from app.infrastructure.websocket import UserConnectionManager, WSBroker
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
        user_service: UserService,
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
        self._user_service = user_service

    async def execute(
        self,
        ws,
        user_id: str,
        session_id: UUID,
    ) -> None:
        # Отписаться от чатов
        chats = await self._chat_service.get_user_chat_ids(user_id)
        for chat_id in chats:
            await self._ws_broker.publish_leave_chat(
                action_type="leave_chat",
                chat_id=chat_id,
                user_id=user_id,
            )

        # Удалить session_key
        await self._session_storage.delete(user_id, session_id)

        # Удалить подключение
        await self._manager.disconnect(ws)

        if not self._manager.is_online(user_id):
            await self._presence.set_offline(user_id)
            await self._ws_broker.publish_user_status(user_id, False, chats)

        try:
            admins = await self._user_service.get_admins()
            for admin in admins:
                if admin.id != user_id:
                    await self._ws_broker.publish_to_user(
                        action_type="user_status",
                        user_id=admin.id,
                        data={"user_id": user_id, "status": True}
                    )
        except Exception as e:
            self.log_error(f"Не удалось разослать статус админам: {e}")

        self.log_info(f"Пользователь {user_id} отключился (session={session_id})")