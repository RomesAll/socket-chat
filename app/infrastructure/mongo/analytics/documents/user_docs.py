from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class UserCreatedDoc:
    """Документ аналитики создания пользователя."""
    user_id: str
    role: str
    email: str
    occurred_at: datetime
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass(frozen=True)
class UserUpdatedDoc:
    """Документ аналитики обновления пользователя."""
    user_id: str
    changed_fields: list[str]
    occurred_at: datetime
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass(frozen=True)
class UserDeletedDoc:
    """Документ аналитики удаления пользователя."""
    user_id: str
    occurred_at: datetime
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass(frozen=True)
class UserPasswordChangedDoc:
    """Документ аналитики смены пароля."""
    user_id: str
    occurred_at: datetime
    created_at: datetime = field(default_factory=datetime.utcnow)