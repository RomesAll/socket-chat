from typing import TypeVar, Callable
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import ValidationError
from starlette.requests import Request
from app.infrastructure.security.jwt_manager import JWTAccessManager, JWTRefreshManager, TResponseToken
from app.shared.dto.audit import RequestMeta
from app.shared.dto.enums import RoleEnum
from app.shared.dto.jwt import JWTBaseToken
from app.shared.dto.jwt import TokenType, JWTAccessTokenResponse, JWTRefreshTokenResponse
from starlette import status
import jwt


TToken = TypeVar('TToken', bound=JWTBaseToken)
security = HTTPBearer()


def __get_payload_token(token: str, decode_token: Callable[[str,], TResponseToken]) -> TResponseToken:
    """
    Функция для получения payload токена и его валидация.

    :param token: Строка токена для декодирования.
    :param decode_token: Функция, которая декодирует токен.
    :return: Валидированный payload токена.
    :raises HTTPException: С кодом 401, если токен просрочен или недействителен и с кодом 400,
    если данные в токене не прошли валидацию или произошла иная ошибка.
    """
    try:
        payload = decode_token(token)
        return payload

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Время жизни токена истекло"
        )

    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Недействительный токен"
        )

    except ValidationError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Неверные данные в токене"
        )

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Передан неверный токен"
        )


def get_access_payload(
        credentials: HTTPAuthorizationCredentials = Depends(security)
) -> JWTAccessTokenResponse:
    """
    Функция для получения payload access токена.

    :param credentials: HTTPBearer объект.
    :return: Валидированный payload access токена.
    :raises HTTPException: С кодом 401, если токен просрочен или недействителен и с кодом 400,
    если данные в токене не прошли валидацию или произошла иная ошибка.
    """
    token = credentials.credentials
    payload = __get_payload_token(token, JWTAccessManager.decode_token)
    if payload.type != TokenType.ACCESS_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Передан неверный тип токена для выполнения действия"
        )
    return payload


def get_refresh_payload(
        credentials: HTTPAuthorizationCredentials = Depends(security)
) -> JWTRefreshTokenResponse:
    """
    Функция для получения payload refresh токена.

    :param credentials: HTTPBearer объект.
    :return: Валидированный payload refresh токена.
    :raises HTTPException: С кодом 401, если токен просрочен или недействителен и с кодом 400,
    если данные в токене не прошли валидацию или произошла иная ошибка.
    """
    token = credentials.credentials
    payload = __get_payload_token(token, JWTRefreshManager.decode_token)
    if payload.type != TokenType.REFRESH_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Передан неверный тип токена для выполнения действия"
        )
    return payload


def require_roles(*roles: RoleEnum):
    """Функция для получения payload access токена с проверкой прав доступа"""
    def _dependency(
            payload: JWTAccessTokenResponse = Depends(get_access_payload)
    ) -> JWTAccessTokenResponse:
        if payload.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Отказано в доступе')
        return payload
    return _dependency


def get_request_meta(request: Request) -> RequestMeta:
    """Собрать контекст запроса для audit."""
    return RequestMeta(
        ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        source="web",
    )