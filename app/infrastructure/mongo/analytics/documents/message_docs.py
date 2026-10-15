from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class MessageSentDoc:
    """Документ аналитики отправки сообщения."""
    message_id: str
    chat_id: str
    sender_id: str | None
    message_type: str
    text_length: int
    occurred_at: datetime
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass(frozen=True)
class MessageEditedDoc:
    """Документ аналитики редактирования сообщения."""
    message_id: str
    chat_id: str
    occurred_at: datetime
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass(frozen=True)
class MessageDeletedDoc:
    """Документ аналитики удаления сообщения."""
    message_id: str
    chat_id: str
    occurred_at: datetime
    created_at: datetime = field(default_factory=datetime.utcnow)