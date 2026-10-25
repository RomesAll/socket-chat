from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class RoomCreatedDoc:
    """Документ аналитики создания комнаты."""
    room_id: str
    title: str
    occurred_at: datetime
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass(frozen=True)
class RoomUpdatedDoc:
    """Документ аналитики обновления комнаты."""
    room_id: str
    changed_fields: list[str]
    occurred_at: datetime
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass(frozen=True)
class RoomDeletedDoc:
    """Документ аналитики удаления комнаты."""
    room_id: str
    occurred_at: datetime
    created_at: datetime = field(default_factory=datetime.utcnow)