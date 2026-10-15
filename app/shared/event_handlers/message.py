from datetime import datetime, timezone
from app.domain.events.message import MessageSent, MessageEdited, MessageDeleted
from app.infrastructure.mongo.analytics.documents import (
    MessageSentDoc,
    MessageDeletedDoc,
    MessageEditedDoc
)
from app.infrastructure.mongo.analytics.repositories import MessageAnalyticsRepository


class MessageSentEvent:
    def __init__(self, repo: MessageAnalyticsRepository):
        self._repo = repo

    async def handle(self, event: MessageSent) -> None:
        await self._repo.insert_sent(MessageSentDoc(
            message_id=str(event.message.id),
            chat_id=str(event.message.chat_id),
            sender_id=event.message.sender_id,
            message_type=event.message.type.value,
            text_length=len(event.message.body_encrypted or ""),
            occurred_at=datetime.now(tz=timezone.utc),
        ))


class MessageEditedEvent:
    def __init__(self, repo: MessageAnalyticsRepository):
        self._repo = repo

    async def handle(self, event: MessageEdited) -> None:
        await self._repo.insert_edited(MessageEditedDoc(
            message_id=str(event.message_id),
            chat_id=str(event.chat_id),
            occurred_at=datetime.now(tz=timezone.utc),
        ))


class MessageDeletedEvent:
    def __init__(self, repo: MessageAnalyticsRepository):
        self._repo = repo

    async def handle(self, event: MessageDeleted) -> None:
        await self._repo.insert_deleted(MessageDeletedDoc(
            message_id=str(event.message_id),
            chat_id=str(event.chat_id),
            occurred_at=datetime.now(tz=timezone.utc),
        ))