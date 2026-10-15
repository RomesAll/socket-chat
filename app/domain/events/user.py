from dataclasses import dataclass
from app.shared.dto.user import UserDtoGet


@dataclass(frozen=True)
class UserCreated:
    """Пользователь создан."""
    user: UserDtoGet


@dataclass(frozen=True)
class UserUpdated:
    """Пользователь обновлён."""
    user: UserDtoGet
    changed_fields: list


@dataclass(frozen=True)
class UserDeleted:
    """Пользователь удалён."""
    user_id: str


@dataclass(frozen=True)
class UserPasswordChanged(UserDeleted):
    """Пароль пользователя изменён."""
    pass