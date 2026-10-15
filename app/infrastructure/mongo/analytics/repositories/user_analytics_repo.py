from dataclasses import asdict
from datetime import datetime, timezone, timedelta
from app.infrastructure.mongo.analytics.documents import (
    UserCreatedDoc,
    UserUpdatedDoc,
    UserDeletedDoc,
    UserPasswordChangedDoc,
)


class UserAnalyticsRepository:
    """Репозиторий аналитики по пользователям."""

    def __init__(self, db):
        self._created = db["analytics_user_created"]
        self._updated = db["analytics_user_updated"]
        self._deleted = db["analytics_user_deleted"]
        self._password_changed = db["analytics_user_password_changed"]

    async def insert_created(self, doc: UserCreatedDoc):
        await self._created.insert_one(asdict(doc))

    async def insert_updated(self, doc: UserUpdatedDoc):
        await self._updated.insert_one(asdict(doc))

    async def insert_deleted(self, doc: UserDeletedDoc):
        await self._deleted.insert_one(asdict(doc))

    async def insert_password_changed(self, doc: UserPasswordChangedDoc):
        await self._password_changed.insert_one(asdict(doc))

    async def count_created_by_day(self, days: int = 30) -> list[dict]:
        """Новые пользователи по дням за N дней."""
        since = datetime.now(tz=timezone.utc) - timedelta(days=days)
        cursor = self._created.aggregate([
            {"$match": {"occurred_at": {"$gte": since}}},
            {"$group": {
                "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$occurred_at"}},
                "count": {"$sum": 1},
            }},
            {"$sort": {"_id": 1}},
        ])
        return [{"day": d["_id"], "count": d["count"]} async for d in cursor]

    async def count_deleted_by_day(self, days: int = 30) -> list[dict]:
        """Удалённые пользователи по дням."""
        since = datetime.now(tz=timezone.utc) - timedelta(days=days)
        cursor = self._deleted.aggregate([
            {"$match": {"occurred_at": {"$gte": since}}},
            {"$group": {
                "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$occurred_at"}},
                "count": {"$sum": 1},
            }},
            {"$sort": {"_id": 1}},
        ])
        return [{"day": d["_id"], "count": d["count"]} async for d in cursor]