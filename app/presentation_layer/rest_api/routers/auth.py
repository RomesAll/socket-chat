from fastapi import APIRouter, Depends, HTTPException, status
from app.business_logic.exceptions import (
    AuthError,
    RefreshTokenInActive,
    VerifyCodeInCorrect
)
from app.presentation_layer.rest_api.commands.auth import (
    RegisterCommand, LoginCommand, VerifyCodeCommand,
)
from app.business_logic.use_cases.auth import (
    LoginWithSendCodeUseCase, VerifyCodeUseCase, RefreshTokenUseCase,
    LogoutUseCase, LogoutAllUseCase, LoginWithoutSendCodeUseCase,
)
from app.business_logic.use_cases.user import RegisterUserUseCase
from app.di.auth import get_refresh_payload, get_request_meta, get_access_payload
from app.di.use_cases import (
    get_register_user_use_case, get_login_with_send_code_use_case,
    get_verify_code_use_case, get_refresh_token_use_case,
    get_logout_use_case, get_logout_all_use_case, get_login_without_send_code_use_case,
)
from app.shared.dto.audit import RequestMeta
from app.shared.dto.auth import (
    LoginDtoRequest, LoginOrRegisterDtoResponse, VerifyCodeRequest, LoginDtoResponse,
)
from app.shared.dto.enums import RoleEnum
from app.shared.dto.jwt import JWTTokenResponse, JWTRefreshTokenResponse
from app.shared.dto.user import UserSaveDTO

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=LoginOrRegisterDtoResponse)
async def register(
    cmd: RegisterCommand,
    request_meta: RequestMeta = Depends(get_request_meta),
    use_case: RegisterUserUseCase = Depends(get_register_user_use_case),
):
    try:
        return await use_case.execute(
            UserSaveDTO(
                id=cmd.user_id,
                display_name=cmd.display_name,
                email=cmd.email,
                password=cmd.password,
                avatar_url=None,
                role=RoleEnum.DEFAULT_USER,
                years_old=None,
                description=None
            ),
            request_meta
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/login", response_model=LoginOrRegisterDtoResponse)
async def login(
    cmd: LoginCommand,
    request_meta: RequestMeta = Depends(get_request_meta),
    use_case: LoginWithSendCodeUseCase = Depends(get_login_with_send_code_use_case),
):
    try:
        return await use_case.execute(
            LoginDtoRequest(user_id=cmd.user_id, password=cmd.password),
            request_meta,
        )
    except AuthError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Неверный логин или пароль")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")


@router.post("/debug/login", response_model=LoginDtoResponse)
async def login_debug(
    cmd: LoginCommand,
    request_meta: RequestMeta = Depends(get_request_meta),
    use_case: LoginWithoutSendCodeUseCase = Depends(get_login_without_send_code_use_case),
):
    try:
        return await use_case.execute(
            LoginDtoRequest(user_id=cmd.user_id, password=cmd.password),
            request_meta,
        )
    except AuthError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Неверный логин или пароль")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")


@router.post("/verify-code", response_model=JWTTokenResponse)
async def verify_code(
    cmd: VerifyCodeCommand,
    request_meta: RequestMeta = Depends(get_request_meta),
    use_case: VerifyCodeUseCase = Depends(get_verify_code_use_case),
):
    try:
        return await use_case.execute(
            VerifyCodeRequest(user_id=cmd.user_id, code=cmd.code),
            request_meta,
        )
    except VerifyCodeInCorrect:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Неверный код подтверждения")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")


@router.post("/refresh", response_model=JWTTokenResponse)
async def refresh(
    payload: JWTRefreshTokenResponse = Depends(get_refresh_payload),
    request_meta: RequestMeta = Depends(get_request_meta),
    use_case: RefreshTokenUseCase = Depends(get_refresh_token_use_case),
):
    try:
        return await use_case.execute(payload, request_meta)
    except RefreshTokenInActive:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Сессия истекла. Войдите снова.")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Ошибка обновления токена")


@router.get("/verify", dependencies=[Depends(get_access_payload)])
async def verify_token():
    return {"status": "ok"}


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    payload: JWTRefreshTokenResponse = Depends(get_refresh_payload),
    request_meta: RequestMeta = Depends(get_request_meta),
    use_case: LogoutUseCase = Depends(get_logout_use_case),
):
    await use_case.execute(payload, request_meta)


@router.post("/logout-all", status_code=status.HTTP_204_NO_CONTENT)
async def logout_all(
    payload: JWTRefreshTokenResponse = Depends(get_refresh_payload),
    request_meta: RequestMeta = Depends(get_request_meta),
    use_case: LogoutAllUseCase = Depends(get_logout_all_use_case),
):
    try:
        await use_case.execute(payload.user_id, request_meta)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка при выходе со всех устройств")