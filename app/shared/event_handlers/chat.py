from datetime import datetime, timezone
from app.domain.events.chat import (
    ChatMemberAdded,
    ChatMemberRemoved,
    ChatMemberRoleChanged,
    ChatOwnershipTransferred,
)
from app.infrastructure.mongo.analytics.documents import (
    ChatMemberRoleChangedDoc,
    ChatMemberRemovedDoc,
    ChatMemberAddedDoc,
    ChatChangeOwnerDoc
)
from app.infrastructure.mongo.analytics.repositories import ChatAnalyticsRepository
from app.infrastructure.redis.cache.room_cache import RoomCache


class SaveRoomMemberEvent:
    """Добавить доменное событие добавление участника комнаты в MongoDB."""

    def __init__(self, repo: ChatAnalyticsRepository):
        self._repo = repo

    async def handle(self, event: ChatMemberAdded):
        await self._repo.insert_member_added(ChatMemberAddedDoc(
            chat_id=str(event.chat_id),
            user_id=event.user_id,
            role=event.role,
            occurred_at=datetime.now(tz=timezone.utc)
        ))


class RemoveRoomMemberEvent:
    """Добавить доменное событие удаление участника комнаты в MongoDB."""

    def __init__(self, repo: ChatAnalyticsRepository):
        self._repo = repo

    async def handle(self, event: ChatMemberRemoved):
        await self._repo.insert_member_removed(ChatMemberRemovedDoc(
            chat_id=str(event.chat_id),
            user_id=event.user_id,
            occurred_at=datetime.now(tz=timezone.utc)
        ))


class RoleChangeEvent:
    """Добавить доменное событие для смены роли участника комнаты в MongoDB."""

    def __init__(self, repo: ChatAnalyticsRepository):
        self._repo = repo

    async def handle(self, event: ChatMemberRoleChanged):
        await self._repo.insert_role_changed(ChatMemberRoleChangedDoc(
            chat_id=str(event.chat_id),
            user_id=event.user_id,
            old_role=event.old_role,
            new_role=event.new_role,
            occurred_at=datetime.now(tz=timezone.utc)
        ))


class ChatOwnershipEvent:
    """Добавить доменное событие для смены владельца комнаты в MongoDB."""

    def __init__(self, repo: ChatAnalyticsRepository):
        self._repo = repo

    async def handle(self, event: ChatOwnershipTransferred):
        await self._repo.insert_change_ownership(ChatChangeOwnerDoc(
            chat_id=str(event.chat_id),
            from_user_id=event.from_user,
            to_user_id=event.to_user,
            occurred_at=datetime.now(tz=timezone.utc)
        ))


class InvalidateRoomCacheOnChatMemberAdded:
    """Сбросить кеш комнаты при добавлении участника (меняется members_count)."""

    def __init__(self, cache: RoomCache):
        self._cache = cache

    async def handle(self, event: ChatMemberAdded) -> None:
        await self._cache.invalidate(event.chat_id)


class InvalidateRoomCacheOnChatMemberRemoved:
    """Сбросить кеш комнаты при удалении участника."""

    def __init__(self, cache: RoomCache):
        self._cache = cache

    async def handle(self, event: ChatMemberRemoved) -> None:
        await self._cache.invalidate(event.chat_id)


class InvalidateRoomCacheOnChatMemberRoleChanged:
    """Сбросить кеш комнаты при смене роли (меняется admins_count)."""

    def __init__(self, cache: RoomCache):
        self._cache = cache

    async def handle(self, event: ChatMemberRoleChanged) -> None:
        await self._cache.invalidate(event.chat_id)


class InvalidateRoomCacheOnChatOwnershipTransferred:
    """Сбросить кеш комнаты при передаче владения."""

    def __init__(self, cache: RoomCache):
        self._cache = cache

    async def handle(self, event: ChatOwnershipTransferred) -> None:
        await self._cache.invalidate(event.chat_id)

