from typing import Generic, TypeVar
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import InvalidSignatureError, DecodeError
from starlette import status
from app.business_logic.jwt_manager import JWTAccessManager, JWTRefreshManager
from app.data_layer.models import RoleEnum
from app.shared.dto.jwt import JWTBaseToken
import jwt
from app.shared.dto.jwt import TokenType, JWTAccessTokenResponse, JWTRefreshTokenResponse


TToken = TypeVar('TToken', bound=JWTBaseToken)
security = HTTPBearer()


class AuthChecker(Generic[TToken]):
    """Проверка access и refresh токена"""
    def __init__(
            self,
            token_type: TokenType,
            allowed_roles: list[RoleEnum],
    ):
        self.token_type = token_type
        self.allowed_roles = allowed_roles

    def __call__(
            self,
            credentials: HTTPAuthorizationCredentials = Depends(security),
    ) -> JWTBaseToken:
        token = credentials.credentials
        try:
            payload = None
            try:
                payload: JWTAccessTokenResponse = JWTAccessManager.decode_token(token)
                if payload.type == TokenType.ACCESS_TOKEN:
                    return payload
            except (InvalidSignatureError, DecodeError):
                pass

            try:
                payload: JWTRefreshTokenResponse = JWTRefreshManager.decode_token(token)
                if payload.type == TokenType.REFRESH_TOKEN:
                    return payload
            except (InvalidSignatureError, DecodeError):
                pass

            if not payload:
                raise HTTPException(status_code=401, detail="Не удалось обработать переданный токен")

            if not payload.user_id or not payload.role:
                raise HTTPException(status_code=401, detail="Неверные данные в токене")

            if payload.role not in self.allowed_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="У вас недостаточно прав для выполнения этого действия"
                )
            if payload.type != self.token_type:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Передан неверный тип токена для выполнения действия"
                )
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Время жизни токена истекло")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Недействительный токен")