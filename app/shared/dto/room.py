from datetime import datetime
from uuid import UUID
from pydantic import BaseModel
from app.data_layer.models import RoomRole
from typing import TYPE_CHECKING
from app.shared.dto.chat import ChatDtoSave


class RoomMemberDtoSave(BaseModel):
    """DTO для сохранения участника комнаты"""
    room_id: UUID
    user_id: str
    role: RoomRole = RoomRole.MEMBER


class RoomDtoSave(BaseModel):
    """DTO для сохранения комнаты"""
    id: UUID
    name: str
    description: str = ''
    avatar_url: str | None = None
    owner_id: str
    is_private: bool = True
    members: list[RoomMemberDtoSave]
    chats: list[ChatDtoSave]


class RoomDtoUpdate(BaseModel):
    """DTO для обновления комнаты"""
    name: str | None = None
    description: str | None = None
    avatar_url: str | None = None
    owner_id: str | None = None
    is_private: bool | None = None


class RoomDtoGet(BaseModel):
    """DTO для получения комнаты"""
    id: UUID
    name: str
    description: str | None
    avatar_url: str | None
    owner_id: str
    is_private: bool
    created_at: datetime
    updated_at: datetime


class RoomMemberDtoGet(BaseModel):
    """DTO для получения участника комнаты"""
    room_id: UUID
    user_id: str
    role: RoomRole
    created_at: datetime
    updated_at: datetime