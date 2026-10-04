from datetime import datetime, timezone
from enum import Enum
from pydantic import BaseModel, SecretStr, Field


class SendType(str, Enum):
    """Причисление с типом отправки кода"""
    EMAIL = 'email'


class LoginDtoRequest(BaseModel):
    """DTO для входа в систему"""
    user_id: str
    password: bytes


class LoginDtoResponse(BaseModel):
    """DTO для ответа после входа, регистрации"""
    code: int | None = None
    type_send: SendType = SendType.EMAIL


class LoginOrRegisterDtoResponse(BaseModel):
    """DTO для получения информации о пользователе после входа или регистрации"""
    send_code: SendType
    time_send: datetime = Field(default_factory=lambda : datetime.now(tz=timezone.utc))


class VerifyCodeRequest(BaseModel):
    """DTO для передачи и проверки кода подтверждения"""
    user_id: str
    code: int


class RefreshVerifyCodeRequest(BaseModel):
    """DTO для обновления кода"""
    user_id: str