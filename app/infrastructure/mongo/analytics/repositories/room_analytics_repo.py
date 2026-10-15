from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from app.infrastructure.mongo.analytics.documents import (
    RoomCreatedDoc,
    RoomUpdatedDoc,
    RoomDeletedDoc,
)


class RoomAnalyticsRepository:
    """Репозиторий аналитики по комнатам."""

    def __init__(self, db):
        self._created = db["analytics_room_created"]
        self._updated = db["analytics_room_updated"]
        self._deleted = db["analytics_room_deleted"]

    async def insert_created(self, doc: RoomCreatedDoc) -> None:
        await self._created.insert_one(asdict(doc))

    async def insert_updated(self, doc: RoomUpdatedDoc) -> None:
        await self._updated.insert_one(asdict(doc))

    async def insert_deleted(self, doc: RoomDeletedDoc) -> None:
        await self._deleted.insert_one(asdict(doc))

    async def count_created_by_day(self, days: int = 30) -> list[dict]:
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