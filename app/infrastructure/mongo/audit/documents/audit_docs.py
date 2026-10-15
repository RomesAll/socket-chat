from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from app.shared.dto.enums import ActionType


@dataclass(frozen=True, slots=True)
class AuditDoc:
    """Документ audit-события."""
    actor_type: ActionType
    actor_id: str
    target_id: str
    old_data: dict[str, Any] | None
    new_data: dict[str, Any]
    context: ContextDoc
    occurred_at: datetime
    created_at: datetime = field(default_factory=lambda :datetime.now(tz=timezone.utc))


@dataclass(frozen=True, slots=True)
class ContextDoc:
    """Документ для храпения метаинформации актора."""
    ip: str
    user_agent: str
    source: str