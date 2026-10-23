from dataclasses import dataclass
from uuid import UUID
from app.shared.dto.message import MessageEncryptedGetDTO


@dataclass(frozen=True)
class MessageSent:
    """Сообщение отправлено."""
    message: MessageEncryptedGetDTO


@dataclass(frozen=True)
class MessageEdited:
    """Сообщение отредактировано."""
    message_id: UUID
    chat_id: UUID
    new_body_encrypted: bytes


@dataclass(frozen=True)
class MessageDeleted:
    """Сообщение удалено."""
    message_id: UUID
    chat_id: UUID