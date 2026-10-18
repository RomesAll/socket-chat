from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from .enums import ActionType


@dataclass(frozen=True, slots=True)
class AuditEvent:
    """Модель audit-события."""
    actor_type: ActionType
    actor_id: str
    target_id: str
    old_data: dict[str, Any] | None
    new_data: dict[str, Any] | None
    context: Context
    occurred_at: datetime
    created_at: datetime = field(default_factory=lambda :datetime.now(tz=timezone.utc))


@dataclass(frozen=True, slots=True)
class Context:
    """Модель для метаинформации актора."""
    ip: str
    user_agent: str
    source: str