from fastapi import APIRouter, Depends
from starlette import status
from starlette.responses import JSONResponse
from app.business_logic.services import UserService
from app.data_layer.models import RoleEnum
from app.presentation_layer.dependencies.auth import AuthChecker
from app.presentation_layer.dependencies.base import get_user_service
from app.shared.dto import UserDtoSave
from app.shared.dto.auth import LoginDtoRequest, SendType
from app.shared.dto.jwt import JWTRefreshTokenResponse, TokenType, JWTTokenResponse
from app.shared.dto.user import UserRegister, UserDtoInfoSave
from bootstrap import get_bootstrap


route = APIRouter()
bootstrap = get_bootstrap()


@route.post(
    path='/auth/login',
    tags=['Auth'],
    summary='Вход в систему',
    operation_id="login_user_operation",
)
async def login_user(
        credentials: LoginDtoRequest,
        type_send: SendType = SendType.EMAIL,
        user_service: UserService = Depends(get_user_service)
):
    result = await user_service.login(credentials, type_send)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            'message': f'Код подтверждения был выслан: {result.type_send.value}',
            'detail': result.model_dump(mode='json')
        }
    )


@route.post(
    path='/auth/register',
    tags=['Auth'],
    summary='Регистрация пользователя',
    description='Добавление нового пользователя в систему',
    operation_id="register_user_operation",
)
async def register_user(
        new_user: UserRegister,
        type_send: SendType = SendType.EMAIL,
        user_service: UserService = Depends(get_user_service)
):
    user_dto_save = UserDtoSave(
        id=new_user.id,
        display_name=new_user.display_name,
        user_info=UserDtoInfoSave(
            id=new_user.id,
            email=new_user.email,
            password=new_user.password.encode(),
            repeat_password=new_user.repeat_password.encode()
        )
    )
    result = await user_service.add_user(user_dto_save, type_send)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            'message': f'Код подтверждения был выслан: {result.type_send.value}',
            'detail': result.model_dump(mode='json')
        }
    )


@route.post(
    path='/auth/tokens/refresh',
    tags=['Auth'],
    summary='Обновление токенов',
    description='Обновление access и refresh токенов',
    operation_id="refresh_tokens_operation",
)
async def refresh_tokens(
        token_info: JWTRefreshTokenResponse = Depends(
            AuthChecker[JWTRefreshTokenResponse](
                token_type=TokenType.REFRESH_TOKEN,
                allowed_roles=[RoleEnum.DEFAULT_USER, RoleEnum.SUPER_ADMIN]
            ),
        ),
        user_service: UserService = Depends(get_user_service)
):
    result: JWTTokenResponse = await user_service.refresh_token(token_info)
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={
            'message': 'Токен успешно обновлен',
            'detail': result.model_dump(mode='json')
        },
        media_type="application/json"
    )


@route.post(
    path='/auth/logout',
    tags=['Auth'],
    summary='Выход из системы',
    description='Выход из системы, удаляет сессионный ключ и id refresh токена из white list',
    operation_id="logout_user_operation",
)
async def logout_user_operation(
        token_info: JWTRefreshTokenResponse = Depends(
            AuthChecker[JWTRefreshTokenResponse](
                token_type=TokenType.REFRESH_TOKEN,
                allowed_roles=[RoleEnum.DEFAULT_USER, RoleEnum.SUPER_ADMIN]
            ),
        ),
        user_service: UserService = Depends(get_user_service)
):
    await user_service.logout(
        user_id=token_info.user_id,
        session_id=token_info.session_id,
        ref_token_id=token_info.refresh_id
    )
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={
            'message': 'Выход из системы успешно выполнен',
        },
        media_type="application/json"
    )