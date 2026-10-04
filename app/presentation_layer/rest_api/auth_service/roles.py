from fastapi import APIRouter, Depends
from starlette import status
from starlette.responses import JSONResponse
from app.business_logic.services import UserService, AuthService
from app.data_layer.models import RoleEnum
from app.presentation_layer.dependencies.auth import AuthChecker
from app.presentation_layer.dependencies.base import get_user_service, get_auth_service
from app.shared.dto.jwt import JWTRefreshTokenResponse, TokenType
from bootstrap import get_bootstrap


route = APIRouter()
bootstrap = get_bootstrap()


@route.post(
    path='/auth/{user_id}/roles/change-role',
    tags=['Auth'],
    summary='Изменение роли для пользователя',
    operation_id="change_role_operation",
)
async def change_role(
        user_id: str,
        role: RoleEnum,
        token_info: JWTRefreshTokenResponse = Depends(
            AuthChecker[JWTRefreshTokenResponse](
                token_type=TokenType.REFRESH_TOKEN,
                allowed_roles=[RoleEnum.SUPER_ADMIN],
            ),
        ),
        auth_service: AuthService = Depends(get_auth_service)
):
    result = await auth_service.change_role(user_id, role, token_info.refresh_id)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            'message': f'Роль успешно изменена',
            'detail': {'user_id': result}
        }
    )


@route.post(
    path='/auth/{user_id}/roles/change-role/master-key',
    tags=['Auth'],
    summary='Изменение роли для пользователя по мастер ключу',
    operation_id="change_role_via_master_key_operation",
)
async def change_role_via_master_key(
        user_id: str,
        role: RoleEnum,
        master_psw: str,
        token_info: JWTRefreshTokenResponse = Depends(
            AuthChecker[JWTRefreshTokenResponse](
                token_type=TokenType.REFRESH_TOKEN,
                allowed_roles=[RoleEnum.SUPER_ADMIN, RoleEnum.DEFAULT_USER],
            ),
        ),
        auth_service: AuthService = Depends(get_auth_service)
):
    result = await auth_service.change_role_by_psw(user_id, role, master_psw, token_info.refresh_id)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            'message': f'Роль успешно изменена',
            'detail': {'user_id': result}
        }
    )