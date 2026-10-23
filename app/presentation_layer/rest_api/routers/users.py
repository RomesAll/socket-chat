from fastapi import (
    APIRouter,
    Depends
)
from fastapi import Query
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
    UserDtoBriefGet,
    UserUpdateDTO, UserSaveDTO, UserEncryptedSaveDTO
)


router = APIRouter(prefix="/users", tags=["users"])


@router.get("/", dependencies=[Depends(require_admins)])
async def list_users(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    service: UserService = Depends(get_user_service),
):
    return await service.get_many(limit, offset)


@router.get("/me/profile", response_model=UserDtoGet)
async def get_me_info(
    user_id: str = Depends(get_user_id),
    service: UserService = Depends(get_user_service),
):
    return await service.get(user_id=user_id)


@router.get("/{user_id}/profile", response_model=UserDtoGet, dependencies=[Depends(require_admins)])
async def get_user_profile(
    user_id: str,
    service: UserService = Depends(get_user_service),
):
    return await service.get(user_id)


@router.get("/{user_id}/profile/brief", dependencies=[Depends(require_authorized)])
async def get_user_brief(
    user_id: str,
    service: UserService = Depends(get_user_service),
):
    result = await service.get_brief(user_id=user_id)
    return result


@router.post('/debug', dependencies=[Depends(require_admins)])
async def create_user_debug(
    cmd: RegisterCommand,
    service: UserService = Depends(get_user_service)
):
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


@router.patch("/{user_id}", response_model=UserDtoGet)
async def update_user(
    user_id: str,
    cmd: UpdateUserCommand,
    actor_id: str = Depends(get_user_id),
    request_meta: RequestMeta = Depends(get_request_meta),
    use_case: UpdateUserUseCase = Depends(get_update_user_use_case),
):
    return await use_case.execute(
        user_id=user_id,
        dto=UserUpdateDTO(**cmd.model_dump(exclude_unset=True)),
        actor_id=actor_id,
        request_meta=request_meta,
    )


@router.delete("/{user_id}", response_model=UserDtoGet)
async def delete_user(
    user_id: str,
    actor_id = Depends(get_user_id),
    request_meta: RequestMeta = Depends(get_request_meta),
    use_case: DeleteUserUseCase = Depends(get_delete_user_use_case),
):
    return await use_case.execute(user_id, actor_id, request_meta)


@router.patch("/{user_id}/password", response_model=UserDtoGet)
async def change_password(
    user_id: str,
    cmd: ChangePasswordCommand,
    actor_id = Depends(get_user_id),
    request_meta: RequestMeta = Depends(get_request_meta),
    use_case: ChangeUserPasswordUseCase = Depends(get_change_user_password_use_case),
):
    return await use_case.execute(
        user_id=user_id,
        old_password=cmd.old_password,
        new_password=cmd.new_password,
        actor_id=actor_id,
        request_meta=request_meta,
    )


@router.patch("/{user_id}/role", response_model=UserDtoGet, dependencies=[Depends(require_admins)])
async def change_role(
    user_id: str,
    new_role: str,
    actor_id = Depends(get_user_id),
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
    role = RoleEnum(role)
    return await use_case.execute(
        user_id=user_id,
        new_role=role,
        actor_id=actor_id,
        request_meta=request_meta,
    )


@router.patch("/debug/{user_id}/role", response_model=UserDtoGet)
async def change_role_by_secret_key(
    user_id: str,
    new_role: RoleEnum,
    secret_key: str,
    service: UserService = Depends(get_user_service),

):
    if get_config().app_key != secret_key:
        raise Exception
    return await service.update_role(
        user_id=user_id,
        new_role=new_role,
    )


@router.get('/{user_id}/is_online', dependencies=[Depends(require_authorized)])
async def is_online(
    user_id: str,
    service: PresenceService = Depends(get_presence_service)
):
    user_is_online = await service.is_online(user_id)
    return {'user_id': user_id, 'status': user_is_online}
