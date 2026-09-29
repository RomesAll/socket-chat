from uuid import UUID
from starlette.websockets import WebSocketState, WebSocket


class UserConnectionManager:
    """
    Класс менеджер для управления подключениями пользователей
    """
    def __init__(self):
        self.active_session: dict[str, dict[UUID, WebSocket]] = {}
        self._ws_user_session: dict[WebSocket, tuple[str, UUID]] = {}
        self._chats: dict[UUID, set[WebSocket]] = {}
        self._ws_chats: dict[WebSocket, set[UUID]] = {}

    async def connection(self, ws: WebSocket, user_id: str, session_id: UUID):
        """Принятие и регистрация соединений"""
        await ws.accept()
        self.active_session.setdefault(user_id, {})[session_id] = ws
        self._ws_user_session[ws] = (user_id, session_id)

    async def disconnect(self, ws: WebSocket):
        """Отключение соединения клиента"""
        user_id, user_session = self._ws_user_session.pop(ws, (None, None))
        if not user_id or not user_session:
            return None
        user_sessions = self.active_session.get(user_id)
        if user_sessions:
            user_sessions.pop(user_session, None)
            if not user_sessions:
                self.active_session.pop(user_id, None)

        for chat_id in self._ws_chats.pop(ws, set()):
            chat_ws: set[WebSocket] | None = self._chats.get(chat_id)
            if chat_ws:
                chat_ws.discard(ws)
                if not chat_ws:
                    self._chats.pop(chat_id, None)

        try:
            if ws.client_state != WebSocketState.DISCONNECTED:
                await ws.close()
        except Exception:
            pass

    def join_in_chat(self, ws: WebSocket, chat_id: UUID):
        """Добавить сокет в чат"""
        self._chats.setdefault(chat_id, set()).add(ws)
        self._ws_chats.setdefault(ws, set()).add(chat_id)

    def leave_chat(self, ws: WebSocket, chat_id: UUID):
        """Отписать сокет от чата"""
        chat_ws = self._chats.get(chat_id)
        if chat_ws:
            chat_ws.discard(ws)
            if not chat_ws:
                self._chats.pop(chat_id, None)

        ws_chats = self._ws_chats.get(ws)
        if ws_chats:
            ws_chats.discard(chat_id)
            if not ws_chats:
                self._ws_chats.pop(ws, None)

    def leave_all_chats(self, ws: WebSocket):
        """Отписать соединение от всех чатов"""
        for chat_id in self._ws_chats.pop(ws, set()):
            chat_ws = self._chats.get(chat_id)
            if chat_ws:
                chat_ws.discard(ws)
                if not chat_ws:
                    self._chats.pop(chat_id, None)

    async def _send_message(self, ws: WebSocket, payload: dict) -> bool:
        """Отправить сообщение, если произошла ошибка, то отключить сокет."""
        try:
            await ws.send_json(payload)
            return True
        except Exception:
            await self.disconnect(ws)
            return False

    async def send_to_chat(self, chat_id: UUID, payload: dict) -> int:
        """
        Отправить сообщение пользователям ws, подписанным на чат
        :param chat_id: id пользователей
        :param payload: тело сообщения
        :return: кол-во отправленных сообщений
        """
        ws_connections = list(self._chats.get(chat_id, ()))
        count_send = 0
        for ws in ws_connections:
            if await self._send_message(ws, payload):
                count_send += 1
        return count_send

    async def send_to_user(self, user_id: str, payload: dict) -> int:
        """Отправить сообщение во все сессии пользователя"""
        sessions = list(self.active_session.get(user_id, {}).values())
        count_send = 0
        for ws in sessions:
            if await self._send_message(ws, payload):
                count_send += 1
        return count_send

    async def send_to_session(self, user_id: str, session_id: UUID, payload: dict) -> bool:
        """Отправить сообщение в конкретную сессию пользователя"""
        sessions = self.active_session.get(user_id)
        if not sessions:
            return False
        ws = sessions.get(session_id)
        if ws is None:
            return False
        return await self._send_message(ws, payload)

    async def broadcast(self, payload: dict) -> int:
        """Отправить сообщение всем соединениям"""
        connections = list(self._ws_user_session.keys())
        count_send = 0
        for ws in connections:
            if await self._send_message(ws, payload):
                count_send += 1
        return count_send

