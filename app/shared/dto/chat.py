from uuid import UUID
from pydantic import BaseModel


class ChatDtoSave(BaseModel):
    """DTO для сохранения чата"""
    id: UUID
    name: str
    room_id: UUID
    members: list[ChatMemberDtoSave]


class ChatMemberDtoSave(BaseModel):
    """DTO для сохранения участника чата"""
    chat_id: UUID
    user_id: str


class ChatDtoUpdate(BaseModel):
    """DTO для обновления чата"""
    name: str | None = None


class ChatMemberDtoUpdate(BaseModel):
    """DTO для обновления участника чата"""
    last_read_message_id: UUID | None = None
    mute: bool | None = None