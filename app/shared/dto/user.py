from app.shared.dto.base import BaseSaveDTO, _UnsetType, UNSET, BaseUpdateDTO
from app.shared.dto.enums import RoleEnum
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class BaseUserSaveDTO:
    """Базовый DTO для сохранения пользователя."""
    id: str
    display_name: str
    email: str
    avatar_url: str | None
    description: str | None
    years_old: int | None
    role: RoleEnum


@dataclass(frozen=True, slots=True)
class UserSaveDTO(BaseUserSaveDTO, BaseSaveDTO):
    """DTO для хранения данных нового пользователя с открытым паролем."""
    password: str


@dataclass(frozen=True, slots=True)
class UserEncryptedSaveDTO(BaseUserSaveDTO, BaseSaveDTO):
    """DTO для хранения данных нового пользователя с хешем пароля."""
    password: bytes


@dataclass(frozen=True, slots=True)
class UserUpdateDTO(BaseUpdateDTO):
    """DTO для обновления базовой информации пользователя."""
    display_name: str | None | _UnsetType= UNSET
    avatar_url: str | None | _UnsetType= UNSET
    description: str | None | _UnsetType= UNSET
    years_old: int | None | _UnsetType= UNSET


@dataclass(frozen=True, slots=True)
class UserDtoBriefGet:
    """DTO для получения общей информации о пользователе."""
    id: str
    display_name: str
    avatar_url: str | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class UserDtoGet(UserDtoBriefGet):
    """DTO для получения информации о пользователе."""
    description: str | None
    years_old: int | None
    role: RoleEnum
    email: str
    last_seen_at: datetime | None