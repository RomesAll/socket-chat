from datetime import datetime
from uuid import UUID
from pydantic import BaseModel
from app.data_layer.models import MessageType


class MessageDtoSave(BaseModel):
    """DTO для сохранения сообщений"""
    id: UUID
    chat_id: UUID
    sender_id: str
    body_encrypted: str
    type: MessageType
    reply_to_message_id: UUID | None = None
    forwarded_from_message_id: UUID | None = None
    forwarded_from_user_id: str | None = None
    is_edited: bool = False
    message_file: list[MessageAttachmentDtoSave] | None = None


class MessageDtoGet(MessageDtoSave):
    """DTO для получения сохраненного сообщения"""
    created_at: datetime
    updated_at: datetime
    is_deleted: bool = False
    deleted_at: datetime | None = None


class MessageDtoUpdate(BaseModel):
    """DTO для обновления сообщений"""
    body_encrypted: str | None = None
    is_edited: bool | None = None
    is_deleted: bool | None = None


class MessageAttachmentDtoSave(BaseModel):
    """DTO для сохранения файлов"""
    id: UUID
    message_id: UUID
    file_name: str
    file_path: str
    mime_type: str
    size: int