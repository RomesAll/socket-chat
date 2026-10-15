from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass(frozen=True)
class ChatMemberAddedDoc:
    """Документ аналитики добавления участника в чат."""
    chat_id: str
    user_id: str
    role: str
    occurred_at: datetime
    created_at: datetime = field(default_factory=lambda :datetime.now(tz=timezone.utc))


@dataclass(frozen=True)
class ChatMemberRemovedDoc:
    """Документ аналитики удаления участника из чата."""
    chat_id: str
    user_id: str
    occurred_at: datetime
    created_at: datetime = field(default_factory=lambda :datetime.now(tz=timezone.utc))


@dataclass(frozen=True)
class ChatMemberRoleChangedDoc:
    """Документ аналитики смены роли участника."""
    chat_id: str
    user_id: str
    old_role: str
    new_role: str
    occurred_at: datetime
    created_at: datetime = field(default_factory=lambda :datetime.now(tz=timezone.utc))


@dataclass(frozen=True)
class ChatChangeOwnerDoc:
    """Документ аналитики передачи владения."""
    chat_id: str
    from_user_id: str
    to_user_id: str
    occurred_at: datetime
    created_at: datetime = field(default_factory=lambda :datetime.now(tz=timezone.utc))