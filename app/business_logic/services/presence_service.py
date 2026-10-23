from app.infrastructure.redis import PresenceCache
from app.infrastructure.websocket import UserConnectionManager


class PresenceService:
    """Сервис для работы со статусом пользователей"""

    def __init__(
            self,
            cache: PresenceCache,
            conn_manager: UserConnectionManager
    ):
        self._cache = cache
        self._conn_manager = conn_manager

    async def is_online(self, user_id: str) -> bool:
        """Проверить статус пользователя"""
        if not (is_online := self._conn_manager.is_online(user_id)):
            return await self._cache.is_online(user_id)
        return is_online