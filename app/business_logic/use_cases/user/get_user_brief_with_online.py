from app.business_logic.services import UserService
from app.infrastructure.redis import PresenceCache
from app.shared.dto.user import UserDtoGetWithOnlineStatus


class GetUserBriefInfoUseCase:
    """
    Получить профиль пользователя с онлайн-статусом.

    Сценарий:
    - Получить информацию о пользователе.
    - Получить online-статус из кеша.
    """

    def __init__(
        self,
        user_service: UserService,
        presence_cache: PresenceCache,
    ):
        self._user_service = user_service
        self._presence_cache = presence_cache

    async def execute(self, user_id: str) -> UserDtoGetWithOnlineStatus:
        # Получить пользователя
        user = await self._user_service.get(user_id)

        # Получить online статус
        is_online = await self._presence_cache.is_online(user_id)

        return UserDtoGetWithOnlineStatus(
            user=user.to_brief(),
            is_online=is_online,
        )