from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status
)
from fastapi import Query
from app.business_logic.exceptions import AuthError, PermissionError
from app.business_logic.services import UserService
from app.business_logic.services.presence_service import PresenceService
from app.presentation_layer.rest_api.commands import RegisterCommand
from app.presentation_layer.rest_api.commands.users import (
    UpdateUserCommand,
    ChangePasswordCommand,
)
from app.business_logic.use_cases.user import (
    UpdateUserUseCase,
    DeleteUserUseCase,
    ChangeUserRoleUseCase,
    ChangeUserPasswordUseCase,
)
from app.di.auth import (
    get_request_meta,
    get_user_id,
    require_admins, require_authorized,
)
from app.di.dependencies import get_user_service, get_presence_service
from app.di.use_cases import (
    get_update_user_use_case,
    get_delete_user_use_case,
    get_change_user_role_use_case,
    get_change_user_password_use_case,
)
from app.shared.config import get_config
from app.shared.dto.audit import RequestMeta
from app.shared.dto.enums import RoleEnum
from app.shared.dto.user import (
    UserDtoGet,
    UserUpdateDTO,
    UserEncryptedSaveDTO
)
from app.infrastructure.database.exceptions import DBError

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/", dependencies=[Depends(require_admins)])
async def list_users(
        limit: int = Query(50, ge=1, le=200),
        offset: int = Query(0, ge=0),
        service: UserService = Depends(get_user_service),
):
    try:
        return await service.get_many(limit, offset)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Ошибка получения списка пользователей")


@router.get("/me/profile", response_model=UserDtoGet)
async def get_me_info(
        user_id: str = Depends(get_user_id),
        service: UserService = Depends(get_user_service),
):
    try:
        return await service.get(user_id=user_id)
    except DBError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")


@router.get("/{user_id}/profile", response_model=UserDtoGet, dependencies=[Depends(require_admins)])
async def get_user_profile(
        user_id: str,
        service: UserService = Depends(get_user_service),
):
    try:
        return await service.get(user_id)
    except DBError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")


@router.get("/{user_id}/profile/brief", dependencies=[Depends(require_authorized)])
async def get_user_brief(
        user_id: str,
        service: UserService = Depends(get_user_service),
):
    try:
        return await service.get_brief(user_id=user_id)
    except DBError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")


@router.post('/debug', dependencies=[Depends(require_admins)])
async def create_user_debug(
        cmd: RegisterCommand,
        service: UserService = Depends(get_user_service)
):
    try:
        encrypt_psw = service.hash_password(cmd.password)
        user = await service.save(UserEncryptedSaveDTO(
            id=cmd.user_id,
            display_name=cmd.display_name,
            email=cmd.email,
            avatar_url=None,
            description=None,
            years_old=None,
            role=RoleEnum.DEFAULT_USER,
            password=encrypt_psw
        ))
        return user
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Пользователь уже существует или неверные данные")


@router.patch("/{user_id}", response_model=UserDtoGet)
async def update_user(
        user_id: str,
        cmd: UpdateUserCommand,
        actor_id: str = Depends(get_user_id),
        request_meta: RequestMeta = Depends(get_request_meta),
        use_case: UpdateUserUseCase = Depends(get_update_user_use_case),
):
    try:
        return await use_case.execute(
            user_id=user_id,
            dto=UserUpdateDTO(**cmd.model_dump(exclude_unset=True)),
            actor_id=actor_id,
            request_meta=request_meta,
        )
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except DBError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ошибка обновления профиля")


@router.delete("/{user_id}", response_model=UserDtoGet)
async def delete_user(
        user_id: str,
        actor_id=Depends(get_user_id),
        request_meta: RequestMeta = Depends(get_request_meta),
        use_case: DeleteUserUseCase = Depends(get_delete_user_use_case),
):
    try:
        return await use_case.execute(user_id, actor_id, request_meta)
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except DBError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ошибка удаления пользователя")


@router.patch("/{user_id}/password", response_model=UserDtoGet)
async def change_password(
        user_id: str,
        cmd: ChangePasswordCommand,
        actor_id=Depends(get_user_id),
        request_meta: RequestMeta = Depends(get_request_meta),
        use_case: ChangeUserPasswordUseCase = Depends(get_change_user_password_use_case),
):
    try:
        return await use_case.execute(
            user_id=user_id,
            old_password=cmd.old_password,
            new_password=cmd.new_password,
            actor_id=actor_id,
            request_meta=request_meta,
        )
    except AuthError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Неверный старый пароль")
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except DBError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ошибка смены пароля")


@router.patch("/{user_id}/role", response_model=UserDtoGet, dependencies=[Depends(require_admins)])
async def change_role(
        user_id: str,
        new_role: str,
        actor_id=Depends(get_user_id),
        request_meta: RequestMeta = Depends(get_request_meta),
        use_case: ChangeUserRoleUseCase = Depends(get_change_user_role_use_case),
):
    role: RoleEnum | None = None
    match new_role:
        case 'ADMIN':
            role = RoleEnum.ADMIN
        case 'SUPER_ADMIN':
            role = RoleEnum.SUPER_ADMIN
        case 'DEFAULT_USER':
            role = RoleEnum.DEFAULT_USER
        case _:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Неизвестная роль")

    role = RoleEnum(role)

    try:
        return await use_case.execute(
            user_id=user_id,
            new_role=role,
            actor_id=actor_id,
            request_meta=request_meta,
        )
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except DBError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ошибка смены роли")


@router.patch("/debug/{user_id}/role", response_model=UserDtoGet)
async def change_role_by_secret_key(
        user_id: str,
        new_role: RoleEnum,
        secret_key: str,
        service: UserService = Depends(get_user_service),
):
    if get_config().app_key != secret_key:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Неверный секретный ключ")
    try:
        return await service.update_role(
            user_id=user_id,
            new_role=new_role,
        )
    except DBError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")


@router.get('/{user_id}/is_online', dependencies=[Depends(require_authorized)])
async def is_online(
        user_id: str,
        service: PresenceService = Depends(get_presence_service)
):
    try:
        user_is_online = await service.is_online(user_id)
        return {'user_id': user_id, 'status': user_is_online}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Не удалось получить статус пользователя")