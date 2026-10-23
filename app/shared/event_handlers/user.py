from datetime import datetime, timezone
from app.domain.events.user import (
    UserCreated,
    UserUpdated,
    UserDeleted,
    UserPasswordChanged, UserUpdatedRole,
)
from app.infrastructure.redis.cache.user_cache import UserCache
from app.infrastructure.redis.jwt_white_list import JWTWhiteListCache
from app.infrastructure.mongo.analytics.documents import (
    UserUpdatedDoc,
    UserPasswordChangedDoc,
    UserDeletedDoc,
    UserCreatedDoc
)
from app.infrastructure.mongo.analytics.repositories import UserAnalyticsRepository


class SaveUserEvent:
    """Обработчик события сохранения пользователя для аналитики в Mongodb"""

    def __init__(self, repo: UserAnalyticsRepository):
        self._repo = repo

    async def handle(self, event: UserCreated):
        await self._repo.insert_created(UserCreatedDoc(
            user_id=event.user.id,
            role=event.user.role,
            email=event.user.email,
            occurred_at=datetime.now(tz=timezone.utc),
        ))


class SaveUserToCacheOnUserCreated:
    """Обработчик события сохранения пользователя для кеша в Redis"""

    def __init__(self, cache: UserCache):
        self._cache = cache

    async def handle(self, event: UserCreated) -> None:
        await self._cache.save(event.user)


class UpdateUserEvent:
    """Обработчик события обновления пользователя для аналитики в Mongodb"""

    def __init__(self, repo: UserAnalyticsRepository):
        self._repo = repo

    async def handle(self, event: UserUpdated):
        await self._repo.insert_updated(UserUpdatedDoc(
            user_id=event.user.id,
            changed_fields=event.changed_fields,
            occurred_at=datetime.now(tz=timezone.utc)
        ))


class InvalidateUserCacheOnUserUpdated:
    """Обработчик события обновления пользователя для инвалидации кеша в Redis"""

    def __init__(self, cache: UserCache):
        self._cache = cache

    async def handle(self, event: UserUpdated) -> None:
        await self._cache.delete(event.user.id)


class DeleteUserEvent:
    """Добавить доменное событие удаление пользователя в MongoDB."""

    def __init__(self, repo: UserAnalyticsRepository):
        self._repo = repo

    async def handle(self, event: UserDeleted):
        await self._repo.insert_deleted(UserDeletedDoc(
            user_id=event.user_id,
            occurred_at=datetime.now(tz=timezone.utc)
        ))


class InvalidateUserCacheOnUserDeleted:
    """Обработчик события удаления пользователя для инвалидации кеша в Redis"""

    def __init__(self, cache: UserCache):
        self._cache = cache

    async def handle(self, event: UserDeleted) -> None:
        await self._cache.delete(event.user_id)


class RevokeAllTokensOnUserDeleted:
    """Обработчик события удаления пользователя для отзыва всех refresh-токены пользователя в Redis."""

    def __init__(self, jwt_white_list: JWTWhiteListCache):
        self._jwt_white_list = jwt_white_list

    async def handle(self, event: UserDeleted) -> None:
        await self._jwt_white_list.clear_user_token(event.user_id)


class ChangePswUserEvent:
    """Добавить доменное событие обновления пользователя в MongoDB."""

    def __init__(self, repo: UserAnalyticsRepository):
        self._repo = repo

    async def handle(self, event: UserPasswordChanged):
        await self._repo.insert_password_changed(UserPasswordChangedDoc(
            user_id=event.user_id,
            occurred_at=datetime.now(tz=timezone.utc)
        ))


class RevokeAllTokensOnUserPasswordChanged:
    """Отозвать все refresh-токены при смене пароля."""

    def __init__(self, jwt_white_list: JWTWhiteListCache):
        self._jwt_white_list = jwt_white_list

    async def handle(self, event: UserPasswordChanged) -> None:
        await self._jwt_white_list.clear_user_token(event.user_id)


class RevokeAllTokensOnUserRoleChanged:
    """Отозвать все refresh-токены при смене роли."""

    def __init__(self, jwt_white_list: JWTWhiteListCache):
        self._jwt_white_list = jwt_white_list

    async def handle(self, event: UserUpdatedRole) -> None:
        await self._jwt_white_list.clear_user_token(event.user_id)


class InvalidateUserCacheChangePsw:
    """Обработчик события удаления пользователя для инвалидации кеша в Redis"""

    def __init__(self, cache: UserCache):
        self._cache = cache

    async def handle(self, event: UserPasswordChanged) -> None:
        await self._cache.delete(event.user_id)


class InvalidateUserCacheChangeRole:
    """Обработчик события удаления пользователя для инвалидации кеша в Redis"""

    def __init__(self, cache: UserCache):
        self._cache = cache

    async def handle(self, event: UserUpdatedRole) -> None:
        await self._cache.delete(event.user_id)