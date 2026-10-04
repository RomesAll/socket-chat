from fastapi import APIRouter, Depends
from starlette import status
from starlette.responses import JSONResponse
from app.business_logic.services import AuthService
from app.presentation_layer.dependencies.base import get_auth_service
from app.shared.dto.auth import VerifyCodeRequest, SendType
from bootstrap import get_bootstrap


route = APIRouter()
bootstrap = get_bootstrap()


@route.post(
    path='/auth/verify-code',
    tags=['Auth'],
    summary='Ввод кода подтверждения',
    description='Ввод кода подтверждения после auth и регистрации',
    operation_id="verify_operation",
)
async def verify_code(
        request: VerifyCodeRequest,
        auth_service: AuthService = Depends(get_auth_service)
):
    result = await auth_service.verify_code(request)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            'message': f'Код подтверждения успешно подтвержден',
            'detail': result.model_dump(mode='json')
        }
    )


@route.post(
    path='/auth/refresh-verify-code',
    tags=['Auth'],
    summary='Обновление кода подтверждения',
    description='Обновление кода подтверждения',
    operation_id="refresh_verify_code_operation",
)
async def refresh_verify_code(
        user_id: str,
        send_type: SendType,
        auth_service: AuthService = Depends(get_auth_service)
):
    result = await auth_service.refresh_verify_code(user_id, send_type)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            'message': f'Код подтверждения успешно обновлен',
            'detail': result.model_dump(mode='json')
        }
    )