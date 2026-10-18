from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class InviteTokenDoc:
    """Токен для вступления в комнату."""
    token: str
    room_id: str
    created_by: str
    expires_at: datetime
    max_uses: int | None = None
    used_count: int = 0
    is_revoked: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)