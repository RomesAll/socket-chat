from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from app.business_logic.exceptions import (
    PermissionError,
    AlreadyExistsError,
)
from app.business_logic.use_cases.chat import (
    GenerateInviteLinkUseCase,
    JoinByInviteUseCase,
)
from app.di.auth import (
    get_access_payload,
    get_request_meta
)
from app.di.use_cases import (
    get_generate_invite_link_use_case,
    get_join_by_invite_use_case,
)
from app.presentation_layer.rest_api.commands.invite import GenerateInviteCommand
from app.shared.dto.audit import RequestMeta
from app.shared.dto.chat import ChatMemberDTO


router = APIRouter(tags=["invites"])


@router.post(
    "/rooms/{room_id}/invite",
)
async def generate_invite_link(
    room_id: UUID,
    cmd: GenerateInviteCommand,
    payload = Depends(get_access_payload),
    request_meta: RequestMeta = Depends(get_request_meta),
    use_case: GenerateInviteLinkUseCase = Depends(get_generate_invite_link_use_case),
):
    try:
        return await use_case.execute(
            room_id=room_id,
            hours=cmd.hours,
            max_uses=cmd.max_uses,
            actor_id=payload.user_id,
            request_meta=request_meta,
        )
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Не удалось сгенерировать ссылку-приглашение")


@router.post(
    "/invites/{token}/join",
    response_model=ChatMemberDTO,
)
async def join_by_invite(
    token: str,
    payload = Depends(get_access_payload),
    request_meta: RequestMeta = Depends(get_request_meta),
    use_case: JoinByInviteUseCase = Depends(get_join_by_invite_use_case),
):
    try:
        return await use_case.execute(
            token=token,
            actor_id=payload.user_id,
            request_meta=request_meta,
        )
    except AlreadyExistsError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Не удалось вступить в комнату по ссылке")