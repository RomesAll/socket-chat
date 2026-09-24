from datetime import datetime, timezone
from uuid import UUID
from pydantic import BaseModel, Field
from enum import Enum
from app.data_layer.models.users import RoleEnum


class TokenType(str, Enum):
    """Перечисления типов токенов"""
    ACCESS_TOKEN = 'access_token'
    REFRESH_TOKEN = 'refresh_token'


class JWTBaseToken(BaseModel):
    """Base DTO для хранения информации о access и refresh токенах"""
    user_id: str
    sub: str
    type: TokenType
    exp: int | None = None
    session_id: UUID
    role: RoleEnum

    def get_exp_human(self, tz=timezone.utc):
        if not self.exp:
            raise Exception
        return datetime.fromtimestamp(self.exp, tz=tz)


class JWTAccessToken(JWTBaseToken):
    """DTO для хранения информации о access токенах"""
    type: TokenType = Field(default=TokenType.ACCESS_TOKEN)


class JWTRefreshToken(JWTBaseToken):
    """DTO для хранения информации о refresh токенах"""
    refresh_id: UUID
    type: TokenType = Field(default=TokenType.REFRESH_TOKEN)


class JWTBaseResponse(JWTBaseToken):
    """Базовый DTO ответ для отправки jwt токенов"""
    pass


class JWTAccessTokenResponse(JWTBaseResponse):
    """DTO для хранения access jwt токена"""
    type: TokenType = Field(default=TokenType.ACCESS_TOKEN)
    access_token: str


class JWTRefreshTokenResponse(JWTBaseResponse):
    """DTO для хранения refresh jwt токена"""
    refresh_id: UUID
    type: TokenType = Field(default=TokenType.REFRESH_TOKEN)
    refresh_token: str


class JWTTokenResponse(BaseModel):
    """DTO для хранения сгенерированных access и refresh токенах"""
    access_token: str
    refresh_token: str