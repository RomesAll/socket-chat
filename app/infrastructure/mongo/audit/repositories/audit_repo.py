from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from app.domain.events.enums import ActionType
from app.infrastructure.mongo.audit.documents.audit_docs import AuditDoc


class AuditRepository:
    """Репозиторий audit-событий в системе."""

    def __init__(self, db):
        self._collection = db["audit_events"]

    async def insert(self, doc: AuditDoc) -> str:
        """Записать audit-событие. Вернуть _id."""
        result = await self._collection.insert_one(asdict(doc))
        return str(result.inserted_id)

    async def find_by_actor(
        self, actor_id: str, limit: int = 100, offset: int = 0
    ) -> list[dict]:
        """Получить историю действий актора."""
        cursor = (
            self._collection
            .find({"actor_id": actor_id})
            .sort("occurred_at", -1)
            .skip(offset)
            .limit(limit)
        )
        return [doc async for doc in cursor]

    async def find_by_target(
        self, actor_type: ActionType, target_id: str, limit: int = 100, offset: int = 0
    ) -> list[dict]:
        """Получить историю действий над объектом."""
        cursor = (
            self._collection
            .find({"actor_type": actor_type.value, "target_id": target_id})
            .sort("occurred_at", -1)
            .skip(offset)
            .limit(limit)
        )
        return [doc async for doc in cursor]

    async def find_by_action(
        self, action: ActionType, days: int = 30, limit: int = 1000, offset: int = 0
    ) -> list[dict]:
        """Получить все события с указанным действием и временным промежутком."""
        since = datetime.now(tz=timezone.utc) - timedelta(days=days)
        cursor = (
            self._collection
            .find({"action": action.value, "occurred_at": {"$gte": since}})
            .sort("occurred_at", -1)
            .skip(offset)
            .limit(limit)
        )
        return [doc async for doc in cursor]

    async def find_by_request_id(self, request_id: str) -> list[dict]:
        """Получить все события одного клиента по ip."""
        cursor = (
            self._collection
            .find({"context.request_id": request_id})
            .sort("occurred_at", -1)
        )
        return [doc async for doc in cursor]

    async def find_by_actor_target(
            self, actor_id: str, target: str, days: int = 30
    ) -> list[dict]:
        """Получить все события актора над конкретным объектом за промежуток времени."""
        since = datetime.now(tz=timezone.utc) - timedelta(days=days)
        cursor = (
            self._collection
            .find({'actor_id': actor_id, 'target': target, 'occurred_at': {'$gte': since}})
            .sort({'occurred_at', -1})
        )
        return [doc async for doc in cursor]