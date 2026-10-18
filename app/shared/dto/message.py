from datetime import datetime, date
from uuid import UUID
from dataclasses import dataclass
from app.shared.dto.base import BaseSaveDTO
from app.shared.dto.enums import MessageType


@dataclass(frozen=True, slots=True)
class ReplyEncryptedMessageDTO:
    id: UUID
    type: MessageType
    body_encrypted: bytes | None


@dataclass(frozen=True, slots=True)
class ForwardedEncryptedMessageDTO:
    forwarded_from_message_id: UUID
    type: MessageType
    forwarded_from_user_id: str | None
    body_encrypted: bytes | None


@dataclass(frozen=True, slots=True)
class MessageEncryptedGetDTO:
    id: UUID
    chat_id: UUID
    sender_id: str | None
    type: MessageType
    body_encrypted: bytes | None
    reply_to: ReplyEncryptedMessageDTO | None
    forwarded_from: ForwardedEncryptedMessageDTO | None
    is_edited: bool
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class ReplyMessageDTO:
    id: UUID
    type: MessageType
    text: str | None


@dataclass(frozen=True, slots=True)
class ForwardedMessageDTO:
    forwarded_from_message_id: UUID
    forwarded_from_user_id: str | None
    type: MessageType
    text: str | None


@dataclass(frozen=True, slots=True)
class MessageGetDTO:
    id: UUID
    chat_id: UUID
    sender_id: str | None
    type: MessageType
    text: str | None
    reply_to: ReplyMessageDTO | None
    forwarded_from: ForwardedMessageDTO | None
    is_edited: bool
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class SendMessageCommand:
    """Команда отправки сообщения из запроса."""
    chat_id: UUID | None = None
    recipient_id: str | None = None
    type: MessageType = MessageType.TEXT
    text: str | None = None
    reply_to_message_id: UUID | None = None
    forwarded_from_message_id: UUID | None = None
    forwarded_from_user_id: str | None = None


@dataclass(frozen=True, slots=True)
class BaseMessageDTO:
    """DTO для хранения информации о сообщении."""
    id: UUID
    chat_id: UUID
    sender_id: str | None
    type: MessageType
    reply_to_message_id: UUID | None
    forwarded_from_message_id: UUID | None
    forwarded_from_user_id: str | None


@dataclass(frozen=True, slots=True)
class MessageSaveDTO(BaseMessageDTO):
    """DTO для хранения информации о сообщении с открытым текстом сообщения."""
    text: str | None


@dataclass(frozen=True, slots=True)
class MessageEncryptedSavedDTO(BaseMessageDTO, BaseSaveDTO):
    """DTO для хранения информации о сообщении с зашифрованным сообщением."""
    body_encrypted: bytes | None


@dataclass(frozen=True, slots=True)
class MessageAttachmentSaveDTO(BaseSaveDTO):
    """DTO для сохранения информации о медиафайлах сообщения."""
    id: UUID
    message_id: UUID
    file_name: str
    file_path: str
    mime_type: str
    size: int


@dataclass(frozen=True, slots=True)
class MessageAttachmentGetDTO:
    """DTO для получения информации о медиафайлах сообщения."""
    id: UUID
    message_id: UUID
    file_name: str
    file_path: str
    mime_type: str
    size: int
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class MessageEncryptedReadDTO(BaseMessageDTO):
    """Получить информацию о сообщения с зашифрованным текстом сообщения."""
    body_encrypted: bytes | None
    is_edited: bool
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class BaseMessageSenderGroupChat:
    """
    DTO для хранения базовой информации о
    сообщения сгруппированных по чатам
    """
    sender_id: str
    date_limit: date
    count_chats: int


@dataclass(frozen=True, slots=True)
class MessageEncryptedSenderGroupChat(BaseMessageSenderGroupChat):
    """
    Получить информацию о сообщениях с зашифрованным
    текстом сообщения сгруппированных по чатам
    """
    chats: dict[UUID, list[MessageEncryptedReadDTO]]


@dataclass(frozen=True, slots=True)
class MessageSenderGroupChat(BaseMessageSenderGroupChat):
    """
    Получить информацию о сообщения с открытым
    текстом сообщения сгруппированных по чатам
    """
    chats: dict[UUID, list[MessageGetDTO]]