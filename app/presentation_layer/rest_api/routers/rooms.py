from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from app.business_logic.exceptions import PermissionError
from app.business_logic.services import RoomService
from app.business_logic.use_cases.chat import RemoveChatMemberUseCase, ChangeChatMemberRoleUseCase
from app.presentation_layer.rest_api.commands.rooms import CreateRoomCommand, RoomUpdateCommand
from app.business_logic.use_cases.room import (
    CreateRoomUseCase,
    UpdateRoomUseCase,
    DeleteRoomUseCase,
)
from app.di.auth import (
    get_access_payload,
    get_request_meta, get_user_id, require_authorized,
)
from app.di.dependencies import get_room_service
from app.di.use_cases import (
    get_create_room_use_case,
    get_update_room_use_case,
    get_delete_room_use_case, get_remove_chat_member_use_case, get_change_chat_member_role_use_case,
)
from app.shared.dto.audit import RequestMeta
from app.shared.dto.enums import ChatRole
from app.shared.dto.room import RoomDTO, RoomDetailsDTO, RoomUpdateDTO

router = APIRouter(prefix="/rooms", tags=["rooms"])


class ChangeRoleRequest(BaseModel):
    role: ChatRole


@router.post("", response_model=RoomDetailsDTO)
async def create_room(
    cmd: CreateRoomCommand,
    payload = Depends(get_access_payload),
    request_meta: RequestMeta = Depends(get_request_meta),
    use_case: CreateRoomUseCase = Depends(get_create_room_use_case),
):
    try:
        return await use_case.execute(
            title=cmd.title,
            description=cmd.description,
            max_users=cmd.max_users,
            actor_id=payload.user_id,
            request_meta=request_meta,
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Не удалось создать комнату")


@router.get("", response_model=list[RoomDTO])
async def get_rooms(
    limit: int = 20,
    offset: int = 0,
    service: RoomService = Depends(get_room_service),
):
    try:
        return await service.get_many(limit, offset)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка получения списка комнат")


@router.get("/my", response_model=list[RoomDTO])
async def get_my_rooms(
    user_id: str = Depends(get_user_id),
    service = Depends(get_room_service),
):
    try:
        return await service.get_user_rooms(user_id)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка получения ваших комнат")


@router.patch("/{room_id}", response_model=RoomDTO)
async def update_room(
    room_id: UUID,
    cmd: RoomUpdateCommand,
    user_id = Depends(get_user_id),
    request_meta: RequestMeta = Depends(get_request_meta),
    use_case: UpdateRoomUseCase = Depends(get_update_room_use_case),
):
    try:
        return await use_case.execute(
            room_id=room_id,
            dto=RoomUpdateDTO(**cmd.model_dump(exclude_unset=True)),
            actor_id=user_id,
            request_meta=request_meta,
        )
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Комната не найдена")


@router.patch(
    "/{room_id}/members/{user_id}/role",
    dependencies=[Depends(require_authorized)]
)
async def change_member_role(
    room_id: UUID,
    user_id: str,
    cmd: ChangeRoleRequest,
    actor_id: str = Depends(get_user_id),
    request_meta: RequestMeta = Depends(get_request_meta),
    use_case: ChangeChatMemberRoleUseCase = Depends(get_change_chat_member_role_use_case),
):
    try:
        return await use_case.execute(
            chat_id=room_id,
            user_id=user_id,
            new_role=cmd.role,
            actor_id=actor_id,
            request_meta=request_meta
        )
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Не удалось изменить роль участника")


@router.delete("/{room_id}", response_model=RoomDTO)
async def delete_room(
    room_id: UUID,
    payload = Depends(get_access_payload),
    request_meta: RequestMeta = Depends(get_request_meta),
    use_case: DeleteRoomUseCase = Depends(get_delete_room_use_case),
):
    try:
        return await use_case.execute(
            room_id=room_id,
            actor_id=payload.user_id,
            request_meta=request_meta,
        )
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Комната не найдена")


@router.get(
    '/{room_id}/members',
    dependencies=[Depends(require_authorized)]
)
async def get_members(
    room_id: UUID,
    room_service: RoomService = Depends(get_room_service)
):
    try:
        members = await room_service.get_room_members(room_id=room_id)
        return [{"id": m[0], "display_name": m[1], "role": m[2]} for m in members]
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Комната или участники не найдены")


@router.delete('/{room_id}/members/{user_id}')
async def remove_member_in_room(
    room_id: UUID,
    user_id: str,
    actor_id: str = Depends(get_user_id),
    user_case: RemoveChatMemberUseCase = Depends(get_remove_chat_member_use_case),
    request_meta: RequestMeta = Depends(get_request_meta),
):
    try:
        return await user_case.execute(room_id, user_id, actor_id, request_meta)
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Участник или комната не найдены")