from datetime import datetime, timezone
from app.domain.events.message import MessageSent, MessageEdited, MessageDeleted
from app.infrastructure.mongo.analytics.documents import (
    MessageSentDoc,
    MessageDeletedDoc,
    MessageEditedDoc
)
from app.infrastructure.mongo.analytics.repositories import MessageAnalyticsRepository
from app.infrastructure.redis import ChatMessageCache
from app.shared.dto.message import MessageEncryptedReadDTO


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


class MessageSaveToCacheOnMessageCreated:
     """Сохранить сообщение в кеш при создании."""

     def __init__(self, cache: ChatMessageCache):
         self._cache = cache

     async def handle(self, event: MessageSent) -> None:
         await self._cache.push(MessageEncryptedReadDTO(
             id=event.message.id,
             chat_id=event.message.chat_id,
             sender_id=event.message.sender_id,
             type=event.message.type,
             reply_to_message_id=event.message.reply_to_message_id,
             forwarded_from_message_id=event.message.forwarded_from_message_id,
             forwarded_from_user_id=event.message.forwarded_from_user_id,
             body_encrypted=event.message.body_encrypted,
             is_edited=event.message.is_edited,
             created_at=event.message.created_at,
             updated_at=event.message.updated_at
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