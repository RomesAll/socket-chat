from uuid import UUID
from app.infrastructure.redis import SessionKeyStorage
from app.shared.log_config import LogMixin


class SessionService(LogMixin):
    """
    Операции над сессионными ключами WebSocket-подключений.
    """

    def __init__(self, session_key_storage: SessionKeyStorage):
        self._session_key_storage = session_key_storage

    async def save(self, user_id: str, session_id: UUID, session_key: bytes) -> None:
        """
        Сохранить сессионный ключ.

        Алгоритм:\n
        - Делегирует сохранение в SessionKeyStorage.
        - При неудаче SessionKeyStorage кидает SaveSessionKeyError.
        """
        await self._session_key_storage.save(user_id, session_id, session_key)
        self.log_info(f"Сохранён сессионный ключ: user_id={user_id}, session_id={session_id}")

    async def get(self, user_id: str, session_id: UUID) -> bytes:
        """
        Получить сессионный ключ.

        Алгоритм:\n
        - Делегирует получение в SessionKeyStorage.
        - При отсутствии SessionKeyStorage кидает SessionKeyNotFound.
        """
        return await self._session_key_storage.get(user_id, session_id)

    async def delete(self, user_id: str, session_id: UUID) -> None:
        """
        Удалить сессионный ключ.

        Алгоритм:\n
        - Делегирует удаление в SessionKeyStorage.
        - Логирует факт удаления.
        """
        await self._session_key_storage.delete(user_id, session_id)
        self.log_info(f"Удалён сессионный ключ: user_id={user_id}, session_id={session_id}")