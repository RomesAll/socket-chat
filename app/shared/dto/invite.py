from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True, slots=True)
class InviteLinkDTO:
    """Сгенерированная invite-ссылка."""
    token: str
    url: str
    room_id: UUID
    expires_at: datetime
    max_uses: int | None


@dataclass(frozen=True, slots=True)
class InviteTokenInfoDTO:
    """Информация о токене (для проверки)."""
    room_id: UUID
    created_by: str
    expires_at: datetime
    max_uses: int | None
    used_count: int
    is_revoked: bool