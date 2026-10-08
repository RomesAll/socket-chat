from dataclasses import dataclass
from uuid import UUID
from app.shared.dto.base import _UnsetType, UNSET, BaseSaveDTO, BaseUpdateDTO
from app.shared.dto.enums import RoomRole


@dataclass(frozen=True, slots=True)
class RoomSaveDTO(BaseSaveDTO):
    """DTO для сохранения комнаты в БД."""
    id: UUID
    name: str
    description: str | None = None
    avatar_url: str | None = None
    owner_id: str | None = None


@dataclass(frozen=True, slots=True)
class RoomUpdateDTO(BaseUpdateDTO):
    """DTO для обновления комнаты в БД."""
    name: str | None | _UnsetType = UNSET
    description: str | None | _UnsetType = UNSET
    avatar_url: str | None | _UnsetType = UNSET
    owner_id: str | None | _UnsetType = UNSET


@dataclass(frozen=True, slots=True)
class RoomDTO:
    """DTO для получения информации о комнате"""
    id: UUID
    name: str
    description: str | None
    avatar_url: str | None
    owner_id: str | None


@dataclass(frozen=True, slots=True)
class RoomWithUserRoleDTO:
    """DTO для получения информации о комнате, роли пользователя в ней и счетчик участников"""
    id: UUID
    name: str
    avatar_url: str | None
    owner_id: str | None
    role: RoomRole
    members_count: int


@dataclass(frozen=True, slots=True)
class RoomDetailsDTO:
    """DTO для получения детальной информации о комнате и счетчик участников, админов"""
    id: UUID
    name: str
    description: str | None
    avatar_url: str | None
    owner_id: str | None
    members_count: int
    admins_count: int