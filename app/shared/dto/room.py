from uuid import UUID
from pydantic import BaseModel
from app.data_layer.models import RoomRole


class RoomDtoSave(BaseModel):
    """DTO для сохранения комнаты"""
    id: UUID
    name: str
    description: str = ''
    avatar_url: str | None = None
    owner_id: str
    is_private: bool = True
    members: list[RoomMemberDtoSave]


class RoomMemberDtoSave(BaseModel):
    """DTO для сохранения участника комнаты"""
    room_id: UUID
    user_id: str
    role: RoomRole = RoomRole.MEMBER


class RoomDtoUpdate(BaseModel):
    """DTO для обновления комнаты"""
    name: str | None = None
    description: str | None = None
    avatar_url: str | None = None
    owner_id: str | None = None
    is_private: bool | None = None
