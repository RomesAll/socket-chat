from dataclasses import asdict
from datetime import timedelta, timezone, datetime
from uuid import UUID
from bson import Binary, UuidRepresentation
from app.infrastructure.mongo.analytics.documents import (
    MessageSentDoc,
    MessageEditedDoc,
    MessageDeletedDoc,
)


class MessageAnalyticsRepository:
    """Репозиторий аналитики по сообщениям."""

    def __init__(self, db):
        self._sent = db["analytics_message_sent"]
        self._edited = db["analytics_message_edited"]
        self._deleted = db["analytics_message_deleted"]

    async def insert_sent(self, doc: MessageSentDoc) -> None:
        await self._sent.insert_one(asdict(doc))

    async def insert_edited(self, doc: MessageEditedDoc) -> None:
        await self._edited.insert_one(asdict(doc))

    async def insert_deleted(self, doc: MessageDeletedDoc) -> None:
        await self._deleted.insert_one(asdict(doc))

    async def _count_msg(self, base_match: dict, days: int) -> list[dict]:
        """Метод для подсчета сообщений"""
        since = datetime.now(tz=timezone.utc) - timedelta(days=days)
        match = {'occurred_at': {'$gte': since}, **base_match}
        cursor = self._sent.aggregate([
            {'$match': match},
            {'$group': {
                '_id': {'$dateToString': {'format': '%Y-%m-%d', 'date': '$occurred_at'}},
                'count': {'$sum': 1},
            }},
            {'$sort': {'_id': 1}}
        ])
        return [{"day": d["_id"], "count": d["count"]} async for d in cursor]

    async def count_all_msg_send_by_days(self, days: int = 30):
        """Посчитать сообщения по дням (для всех чатов)."""
        return await self._count_msg({}, days)

    async def count_chat_msg_send_by_days(self, chat_id: UUID, days: int = 30):
        """Посчитать сообщения по дням (для чата)."""
        bson_chat_id = Binary.from_uuid(
            chat_id, uuid_representation=UuidRepresentation.STANDARD
        )
        return await self._count_msg({'chat_id': bson_chat_id}, days)

    async def top_senders(self, limit: int = 10) -> list[dict]:
        """Топ отправителей."""
        cursor = self._sent.aggregate([
            {"$group": {"_id": "$sender_id", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": limit},
        ])
        return [{"user_id": d["_id"], "count": d["count"]} async for d in cursor]

    async def top_chats(self, limit: int = 10) -> list[dict]:
        """Топ чатов по сообщениям."""
        cursor = self._sent.aggregate([
            {"$group": {"_id": "$chat_id", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": limit},
        ])
        return [{"chat_id": d["_id"], "count": d["count"]} async for d in cursor]

