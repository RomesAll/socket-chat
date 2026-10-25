from abc import abstractmethod, ABC
from copy import copy
from datetime import timedelta, datetime, timezone
from typing import TypeVar, Generic
from uuid import UUID, uuid4
from app.shared.dto.jwt import JWTAccessToken, JWTRefreshToken, JWTBaseToken, JWTTokenResponse, JWTBaseResponse, JWTAccessTokenResponse, JWTRefreshTokenResponse
from app.infrastructure.database.models.users import RoleEnum
import jwt

TRequestToken = TypeVar('TRequestToken', bound=JWTBaseToken)
TResponseToken = TypeVar('TResponseToken', bound=JWTBaseResponse)


class JWTBaseManager[TRequestToken](ABC):
    def __init__(self, secret_key: str, alg: str, expires_delta: timedelta):
        self._secret_key = secret_key
        self.alg = alg
        self.expires_delta = expires_delta

    def create_token(self, data: TRequestToken) -> str:
        """Создание токена доступа, обновления"""
        to_encode: TRequestToken = copy(data)
        to_encode.exp = int((datetime.now(tz=timezone.utc) + self.expires_delta).timestamp())
        return jwt.encode(to_encode.model_dump(mode='json'), self._secret_key, algorithm=self.alg)

    def decode_token(self, token: str) -> TResponseToken:
        """Декодирование токена доступа, обновления"""
        to_decode = jwt.decode(token, self._secret_key, algorithms=[self.alg,])
        return self._create_token_instance(to_decode_token=to_decode, token=token)

    @classmethod
    @abstractmethod
    def _create_token_instance(cls, to_decode_token: dict, token: str) -> TResponseToken:
        """Создает экземпляр токена (должен быть переопределен)"""
        pass


class JWTAccessManager(JWTBaseManager):
    @classmethod
    def _create_token_instance(cls, to_decode_token: dict, token: str) -> JWTAccessTokenResponse:
        """Создает экземпляр токена"""
        return JWTAccessTokenResponse(**to_decode_token, access_token=token)


class JWTRefreshManager(JWTBaseManager):
    @classmethod
    def _create_token_instance(cls, to_decode_token: dict, token: str) -> JWTRefreshTokenResponse:
        """Создает экземпляр токена"""
        return JWTRefreshTokenResponse(**to_decode_token, refresh_token=token)


class JWTFacade:
    """Фасадный класс для создания access и refresh токенов"""

    def __init__(self, access_manager: JWTAccessManager, refresh_manager: JWTRefreshManager):
        self.jwt_access_manager = access_manager
        self.jwt_refresh_manager = refresh_manager

    def create_tokens(self, user_id: str, sub: str, role: RoleEnum, refresh_id: UUID) -> JWTTokenResponse:
        """Создания пары access и refresh токенов"""
        session_id = uuid4()
        access_token: str = self.jwt_access_manager.create_token(
            JWTAccessToken(
                user_id=user_id,
                sub=sub,
                role=role,
                session_id=session_id
            )
        )
        refresh_token: str = self.jwt_refresh_manager.create_token(
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