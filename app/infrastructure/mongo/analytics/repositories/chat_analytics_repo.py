from dataclasses import asdict
from datetime import timezone, datetime, timedelta
from uuid import UUID
from app.infrastructure.mongo.analytics.documents import (
    ChatMemberAddedDoc,
    ChatMemberRemovedDoc,
    ChatMemberRoleChangedDoc,
    ChatChangeOwnerDoc,
)


class ChatAnalyticsRepository:
    """Репозиторий аналитики по чатам."""

    def __init__(self, db):
        self._member_added = db["analytics_chat_member_added"]
        self._member_removed = db["analytics_chat_member_removed"]
        self._role_changed = db["analytics_chat_member_role_changed"]
        self._ownership = db["analytics_chat_change_ownership"]

    async def insert_member_added(self, doc: ChatMemberAddedDoc):
        await self._member_added.insert_one(asdict(doc))

    async def insert_member_removed(self, doc: ChatMemberRemovedDoc):
        await self._member_removed.insert_one(asdict(doc))

    async def insert_role_changed(self, doc: ChatMemberRoleChangedDoc):
        await self._role_changed.insert_one(asdict(doc))

    async def insert_change_ownership(self, doc: ChatChangeOwnerDoc):
        await self._ownership.insert_one(asdict(doc))

    async def get_added_member(self, chat_id: UUID, days: int = 30) -> list[dict]:
        """Посчитать кол-во добавленных участников"""
        since = datetime.now(tz=timezone.utc) - timedelta(days=days)
        cursor = self._member_added.find({'chat_id': chat_id, 'occurred_at': {'$gte': since}})
        return [member async for member in cursor]

    async def get_removed_member(self, chat_id: UUID, days: int = 30) -> list[dict]:
        """Посчитать кол-во удаленных участников"""
        since = datetime.now(tz=timezone.utc) - timedelta(days=days)
        cursor = self._member_removed.find({'chat_id': chat_id, 'occurred_at': {'$gte': since}})
        return [member async for member in cursor]

    async def find_changed_owner(self, chat_id: UUID) -> list[dict]:
        """Получить информацию о предыдущих владельцев комнаты."""
        cursor = (
            self._ownership
            .find({'chat_id': chat_id})
            .sort({'occurred_at', -1})
        )
        return [member async for member in cursor]

