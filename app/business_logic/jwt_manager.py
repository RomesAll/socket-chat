from abc import abstractmethod, ABC
from copy import copy
from datetime import timedelta, datetime, timezone
from typing import TypeVar, Generic
from uuid import UUID, uuid4
from app.shared.dto.jwt import JWTAccessToken, JWTRefreshToken, JWTBaseToken, JWTTokenResponse, JWTBaseResponse, JWTAccessTokenResponse, JWTRefreshTokenResponse
from app.data_layer.models.users import RoleEnum
import jwt

TRequestToken = TypeVar('TRequestToken', bound=JWTBaseToken)
TResponseToken = TypeVar('TResponseToken', bound=JWTBaseResponse)


class JWTBaseManager(ABC, Generic[TRequestToken, TResponseToken]):
    """Базовый класс менеджер для выпуска и декодирования токенов доступа, обновления"""
    SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"
    EXPIRES_DELTA: timedelta = timedelta(minutes=15)

    @classmethod
    def create_token(cls, data: TRequestToken) -> str:
        """Создание токена доступа, обновления"""
        to_encode: TRequestToken = copy(data)
        to_encode.exp = int((datetime.now(tz=timezone.utc) + cls.EXPIRES_DELTA).timestamp())
        return jwt.encode(to_encode.model_dump(mode='json'), cls.SECRET_KEY, algorithm=cls.ALGORITHM)

    @classmethod
    def decode_token(cls, token: str) -> TResponseToken:
        """Декодирование токена доступа, обновления"""
        to_decode = jwt.decode(token, cls.SECRET_KEY, algorithms=[cls.ALGORITHM,])
        return cls._create_token_instance(to_decode_token=to_decode, token=token)

    @classmethod
    @abstractmethod
    def _create_token_instance(cls, to_decode_token: dict, token: str) -> TResponseToken:
        """Создает экземпляр токена (должен быть переопределен)"""
        pass


class JWTAccessManager(JWTBaseManager[JWTAccessToken, JWTAccessTokenResponse]):
    """Менеджер для выпуска и декодирования токенов доступа"""
    SECRET_KEY: str = "access_secret_key_12345678901234567890"
    EXPIRES_DELTA: timedelta = timedelta(minutes=15)

    @classmethod
    def _create_token_instance(cls, to_decode_token: dict, token: str) -> JWTAccessTokenResponse:
        """Создает экземпляр токена"""
        return JWTAccessTokenResponse(**to_decode_token, access_token=token)


class JWTRefreshManager(JWTBaseManager[JWTRefreshToken, JWTRefreshTokenResponse]):
    """Менеджер для выпуска и декодирования токенов обновления"""
    SECRET_KEY: str = "refresh_secret_key_12345678901234567890"
    EXPIRES_DELTA: timedelta = timedelta(days=7)

    @classmethod
    def _create_token_instance(cls, to_decode_token: dict, token: str) -> JWTRefreshTokenResponse:
        """Создает экземпляр токена"""
        return JWTRefreshTokenResponse(**to_decode_token, refresh_token=token)


class JWTFacade:
    """Фасадный класс для создания access и refresh токенов"""
    jwt_access_manager = JWTAccessManager
    jwt_refresh_manager = JWTRefreshManager

    @classmethod
    def create_tokens(cls, user_id: str, sub: str, role: RoleEnum, refresh_id: UUID) -> JWTTokenResponse:
        """Создания пары access и refresh токенов"""
        session_id = uuid4()
        access_token: str = cls.jwt_access_manager.create_token(
            JWTAccessToken(
                user_id=user_id,
                sub=sub,
                role=role,
                session_id=session_id
            )
        )
        refresh_token: str = cls.jwt_refresh_manager.create_token(
            JWTRefreshToken(
                user_id=user_id,
                sub=sub,
                refresh_id=refresh_id,
                role=role,
                session_id=session_id
            )
        )
        return JWTTokenResponse(
            access_token=access_token,
            refresh_token=refresh_token
        )