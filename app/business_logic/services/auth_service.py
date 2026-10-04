from datetime import datetime, timezone
from uuid import uuid4, UUID

from app.business_logic.exceptions import RefreshTokenInActive, VerifyCodeInCorrect, SaveIdRefreshTokenWhiteListError, \
    VerifyCodeStorageError
from app.business_logic.jwt_manager import JWTFacade
from app.business_logic.psw_manager import PasswordManager
from app.business_logic.redis_adapter import VerifyCodeStorage, Cache, JWTWhiteListCache, SessionKeyStorage
from app.business_logic.websocket import UserConnectionManager
from app.data_layer.models import User, RoleEnum
from app.data_layer.models.events import EventType
from app.business_logic.unit_of_work import UnitOfWork
from app.shared.dto import UserDtoSave
from app.shared.dto.auth import LoginDtoRequest, LoginDtoResponse, SendType, VerifyCodeRequest, VerifyCodeResponse
from app.shared.dto.dto_relation_ship import UserDtoGetWithRel
from app.shared.dto.jwt import JWTRefreshTokenResponse, JWTTokenResponse
from app.shared.dto.room import RoomMemberDtoGet, RoomDtoGet
from app.shared.dto.user import (
    UserDtoGet,
    UserDtoBriefGet,
    RegisterDtoGet,
    UserDtoUpdateDefaultInfo,
    UserDtoUpdateExtendedInfo,
    UserDtoGetWithExtInfo
)
from app.shared.log_config import LogMixin
from app.shared.config import get_config, AppMode, BaseConfig
import random

def _get_config() -> BaseConfig:
    return get_config()


class AuthService(LogMixin):
    """Сервис для управления авторизацией, регистрацией"""
    def __init__(
            self,
            uow: UnitOfWork,
            verify_code_storage: VerifyCodeStorage,
            psw_manager: type[PasswordManager],
            jwt_white_list: JWTWhiteListCache,
            jwt_facade: type[JWTFacade],
            session_key_storage: SessionKeyStorage,
            user_connections: UserConnectionManager
    ):
        self._uow = uow
        self._verify_code_storage = verify_code_storage
        self._psw_manager = psw_manager
        self._jwt_white_list = jwt_white_list
        self._jwt_facade = jwt_facade
        self._session_key_storage = session_key_storage
        self._user_connections = user_connections

    async def verify_code(self, request: VerifyCodeRequest) -> VerifyCodeResponse:
        """Подтверждение кода для получения токенов"""
        async with self._uow as uow:
            user_orm = await uow.user_repo.get_user_by_id(request.user_id)
        if not (await self._verify_code_storage.validate_code(
                user_id=request.user_id,
                code=request.code
        )):
            exc = VerifyCodeInCorrect()
            self.log_error(f'Введенный код подтверждения неверный для пользователя {user_orm.id}')
            raise exc
        refresh_token_id = uuid4()
        jwt_tokens = self._jwt_facade.create_tokens(
            user_orm.id, user_orm.display_name, user_orm.user_info.role, refresh_token_id
        )
        try:
            await self._jwt_white_list.save_refresh_token(
                user_id=user_orm.id,
                token_id=refresh_token_id,
                ex=int((datetime.now(tz=timezone.utc) + JWTFacade.jwt_refresh_manager.EXPIRES_DELTA).timestamp())
            )
            self.log_info(f'Для пользователя {request.user_id} id refresh токена сохранено в white list')
        except SaveIdRefreshTokenWhiteListError:
            self.log_warning(f'Не удалось сохранить id refresh токена в white list, '
                             f'поэтому он будет сохранен во временное хранилище')
        return VerifyCodeResponse(
            refresh_token=jwt_tokens.refresh_token,
            access_token=jwt_tokens.access_token
        )

    async def refresh_verify_code(self, user_id: str, send_type: SendType) -> LoginDtoResponse:
        """Обновление кода подтверждения"""
        async with self._uow as uow:
            user_orm = await uow.user_repo.get_user_by_id(user_id)
            new_code = random.randint(10000, 99999)
            is_code_save = await self._verify_code_storage.save(user_orm.id, new_code)
            if not is_code_save:
                raise VerifyCodeStorageError()
            response = LoginDtoResponse(type_send=send_type)
            if _get_config().mode not in (AppMode.DEV, ):
                if send_type == SendType.EMAIL:
                    uow.add_event(
                        event_name='Send verify code',
                        payload={'to': user_orm.user_info.email, 'code': new_code},
                        event_type=EventType.SEND_VERIFY_CODE
                    )
            else:
                response.code = new_code
            return response

    async def change_role(self, user_id: str, role: RoleEnum, refresh_id: UUID) -> str:
        """Обновить роль пользователя"""
        async with self._uow as uow:
            dto_update = UserDtoUpdateExtendedInfo(role=role)
            updated_user = await uow.user_repo.update_extended_info(user_id, dto_update)
        await self._jwt_white_list.delete_refresh_token(user_id, refresh_id)
        return updated_user.id

    async def change_role_by_psw(self, user_id: str, role: RoleEnum, app_psw: str, refresh_id: UUID) -> str:
        """Обновить роль пользователя по паролю"""
        if app_psw != _get_config().app_key:
            raise Exception
        return await self.change_role(user_id, role, refresh_id)

    async def login(self, cred: LoginDtoRequest, type_send: SendType) -> LoginDtoResponse:
        """Аутентификация пользователя по паре id пользователя и паролю"""
        async with self._uow as uow:
            user_orm: User = uow.user_repo.get_user_by_id(cred.user_id)
            is_eq = self._psw_manager.check_equal_psw(
                cred.password, user_orm.user_info.password
            )
            if not is_eq:
                raise Exception
            code = random.randint(10000, 99999)
            await self._verify_code_storage.save(user_orm.id, code)
            response = LoginDtoResponse(type_send=type_send)
            if _get_config().mode not in (AppMode.DEV, ):
                if type_send == SendType.EMAIL:
                    uow.add_event(
                        event_name='Send verify code',
                        payload={'to': user_orm.user_info.email, 'code': code},
                        event_type=EventType.SEND_VERIFY_CODE
                    )
            else:
                response.code = code
            return response

    async def logout(self, user_id: str, session_id: UUID, ref_token_id: UUID):
        """Выход из системы"""
        await self._jwt_white_list.delete_refresh_token(user_id, ref_token_id)
        await self._session_key_storage.delete(user_id, session_id)
        if sessions := self._user_connections.active_session.get(user_id):
            if ws_connection := sessions.pop(session_id, None):
                await self._user_connections.disconnect(ws_connection)

    async def refresh_token(self, refresh_token: JWTRefreshTokenResponse) -> JWTTokenResponse:
        """Обновление токенов"""
        if not await self._jwt_white_list.is_token_active(
                user_id=refresh_token.user_id,
                token_id=refresh_token.refresh_id
        ):
            exc = RefreshTokenInActive(refresh_token.user_id, refresh_token.refresh_id)
            self.log_error(exc.message)
            raise exc

        new_refresh_id = uuid4()
        self.log_debug(f'Для пользователя {refresh_token.user_id} был '
                       f'сгенерирован id для refresh токена {new_refresh_id}')
        await self._jwt_white_list.update_refresh(
            user_id=refresh_token.user_id,
            old_refresh_id=refresh_token.refresh_id,
            new_refresh_id=new_refresh_id
        )
        self.log_info(f'id refresh токена для пользователя {refresh_token.user_id} '
                      f'успешно обновлен в white list')
        tokens = self._jwt_facade.create_tokens(
            user_id=refresh_token.user_id,
            role=refresh_token.role,
            sub=refresh_token.sub,
            refresh_id=new_refresh_id
        )
        self.log_info(f'Для пользователя {refresh_token.user_id} сгенерирована пара токенов access и refresh')
        return tokens