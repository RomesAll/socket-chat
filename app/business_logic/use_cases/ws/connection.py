from uuid import UUID, uuid4
from app.business_logic.services import ChatService, UserService
from app.infrastructure.redis import PresenceCache, SessionKeyStorage
from app.infrastructure.websocket import UserConnectionManager, WSBroker
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
    ) -> UUID:
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
        chats = await self._chat_service.get_user_chat_ids(user_id)
        for chat_id in chats:
            await self._ws_broker.publish_join_chat(
                action_type="join_chat",
                chat_id=chat_id,
                user_id=user_id,
            )

        await self._ws_broker.publish_user_status(user_id, True, chats)

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

        self.log_info(f"Пользователь {user_id} подключился (session={session_id})")
        return session_id