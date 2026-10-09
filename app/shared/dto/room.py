from datetime import datetime
from dataclasses import dataclass
from uuid import UUID
from app.shared.dto.base import _UnsetType, UNSET, BaseSaveDTO, BaseUpdateDTO
from app.shared.dto.enums import ChatRole


@dataclass(frozen=True, slots=True)
class RoomSaveDTO(BaseSaveDTO):
    """DTO для сохранения комнаты в БД."""
    chat_id: UUID
    title: str
    max_users: int = 30
    description: str | None = None
    avatar_url: str | None = None


@dataclass(frozen=True, slots=True)
class RoomUpdateDTO(BaseUpdateDTO):
    """DTO для обновления комнаты в БД."""
    title: str | None | _UnsetType = UNSET
    max_users: int | None | _UnsetType = UNSET
    description: str | None | _UnsetType = UNSET
    avatar_url: str | None | _UnsetType = UNSET


@dataclass(frozen=True, slots=True)
class RoomDTO:
    """DTO для получения информации о комнате"""
    chat_id: UUID
    title: str
    description: str | None
    avatar_url: str | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class RoomUserMemberDTO:
    """DTO для получения информации о комнате, в которых состоит выбранный пользователь"""
    chat_id: UUID
    title: str
    description: str | None
    avatar_url: str | None
    member_id: str
    role: ChatRole
    members_count: int
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class RoomDetailsDTO:
    """DTO для получения детальной информации о комнате и счетчик участников, админов"""
    chat_id: UUID
    title: str
    max_users: int
    description: str | None
    avatar_url: str | None
    owner_id: str | None
    members_count: int
    admins_count: int
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class GenerateInviteToken:
    """DTO для создания url токена для вступления в группу."""
    actor_id: str
    room_id: UUID
    hours: int
    max_uses: int | None = None