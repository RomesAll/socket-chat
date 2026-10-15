from dataclasses import dataclass
from uuid import UUID
from app.shared.dto.message import MessageGetDTO


@dataclass(frozen=True)
class MessageSent:
    """Сообщение отправлено."""
    message: MessageGetDTO


@dataclass(frozen=True)
class MessageEdited:
    """Сообщение отредактировано."""
    message_id: UUID
    chat_id: UUID
    new_body_encrypted: str


@dataclass(frozen=True)
class MessageDeleted:
    """Сообщение удалено."""
    message_id: UUID
    chat_id: UUID