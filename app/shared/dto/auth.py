from dataclasses import dataclass
from datetime import datetime
from app.shared.dto.enums import SendType, RoleEnum


@dataclass(frozen=True, slots=True)
class LoginDtoRequest:
    """DTO для входа в систему"""
    user_id: str
    password: str


@dataclass(frozen=True, slots=True)
class LoginDtoResponse:
    """DTO для ответа после входа, регистрации"""
    code: int | None = None


@dataclass(frozen=True, slots=True)
class LoginOrRegisterDtoResponse:
    """DTO для получения информации о пользователе после входа или регистрации"""
    send_code: SendType
    time_send: datetime


@dataclass(frozen=True, slots=True)
class VerifyCodeRequest:
    """DTO для передачи и проверки кода подтверждения"""
    user_id: str
    code: int


@dataclass(frozen=True, slots=True)
class RefreshVerifyCodeRequest:
    """DTO для обновления кода"""
    user_id: str


@dataclass(frozen=True, slots=True)
class VerifyCodeResponse:
    """Класс для получения access и refresh токенов"""
    access_token: str
    refresh_token: str


@dataclass(frozen=True, slots=True)
class CreateAuthToken:
    """Класс для создания пары access и refresh токенов"""
    user_id: str
    sub: str
    role: RoleEnum


@dataclass(frozen=True)
class TokensDto:
    access_token: str
    refresh_token: str