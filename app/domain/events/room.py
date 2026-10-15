from dataclasses import dataclass
from uuid import UUID
from app.shared.dto.room import RoomDTO


@dataclass(frozen=True)
class RoomCreated:
    """Комната создана."""
    room: RoomDTO
    owner_id: str


@dataclass(frozen=True)
class RoomUpdated:
    """Комната обновлена."""
    room: RoomDTO
    changed_fields: list


@dataclass(frozen=True)
class RoomDeleted:
    """Комната удалена."""
    room_id: UUID
    owner_id: str