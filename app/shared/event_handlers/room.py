from datetime import datetime, timezone
from app.domain.events.room import RoomCreated, RoomUpdated, RoomDeleted
from app.infrastructure.redis.cache.room_cache import RoomCache
from app.infrastructure.mongo.analytics.documents import (
    RoomUpdatedDoc,
    RoomCreatedDoc,
    RoomDeletedDoc,
)
from app.infrastructure.mongo.analytics.repositories import RoomAnalyticsRepository


class SaveRoomEvent:
    """Добавить доменное событие сохранение комнаты в MongoDB."""

    def __init__(self, repo: RoomAnalyticsRepository):
        self._repo = repo

    async def handle(self, event: RoomCreated):
        await self._repo.insert_created(RoomCreatedDoc(
            room_id=str(event.room.chat_id),
            title=event.room.title,
            occurred_at=datetime.now(tz=timezone.utc),
        ))


class UpdateRoomEvent:
    """Добавить доменное событие обновление комнаты в MongoDB."""

    def __init__(self, repo: RoomAnalyticsRepository):
        self._repo = repo

    async def handle(self, event: RoomUpdated):
        await self._repo.insert_updated(RoomUpdatedDoc(
            room_id=str(event.room.chat_id),
            changed_fields=event.changed_fields,
            occurred_at=datetime.now(tz=timezone.utc)
        ))


class DeleteRoomEvent:
    """Добавить доменное событие удаление комнаты в MongoDB."""

    def __init__(self, repo: RoomAnalyticsRepository):
        self._repo = repo

    async def handle(self, event: RoomDeleted):
        await self._repo.insert_deleted(RoomDeletedDoc(
            room_id=str(event.room_id),
            occurred_at=datetime.now(tz=timezone.utc)
        ))


class SaveRoomToCacheOnRoomCreated:
    """Сохранить комнату в кеш при создании."""

    def __init__(self, cache: RoomCache):
        self._cache = cache

    async def handle(self, event: RoomCreated) -> None:
        await self._cache.save_default(event.room)


class InvalidateRoomCacheOnRoomUpdated:
    """Сбросить кеш комнаты при обновлении."""

    def __init__(self, cache: RoomCache):
        self._cache = cache

    async def handle(self, event: RoomUpdated) -> None:
        await self._cache.invalidate(event.room.chat_id)


class InvalidateRoomCacheOnRoomDeleted:
    """Сбросить кеш комнаты при удалении."""

    def __init__(self, cache: RoomCache):
        self._cache = cache

    async def handle(self, event: RoomDeleted) -> None:
        await self._cache.invalidate(event.room_id)