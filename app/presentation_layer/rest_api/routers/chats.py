from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from app.business_logic.use_cases.chat.delete_chat import DeleteChatUseCase
from app.business_logic.use_cases.chat.get_group_chats import GetGroupChatsUseCase
from app.business_logic.use_cases.chat.get_private_chats import GetPrivateChatsUseCase
from app.di.auth import get_user_id, get_request_meta
from app.di.use_cases import get_private_chats_use_case, get_group_chats_use_case, get_delete_chat_use_case
from app.shared.dto.audit import RequestMeta

router = APIRouter(prefix="/chats", tags=["chats"])


@router.get("/private/me")
async def get_my_private_chats(
    user_id: str = Depends(get_user_id),
    use_case: GetPrivateChatsUseCase = Depends(get_private_chats_use_case)
):
    try:
        return await use_case.execute(user_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось загрузить список приватных чатов"
        )


@router.get("/group/me")
async def get_my_group_chats(
    user_id: str = Depends(get_user_id),
    use_case: GetGroupChatsUseCase = Depends(get_group_chats_use_case)
):
    try:
        return await use_case.execute(user_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось загрузить список групповых чатов"
        )


@router.delete('/{chat_id}')
async def delete_chat(
    chat_id: UUID,
    actor_id: str = Depends(get_user_id),
    use_case: DeleteChatUseCase = Depends(get_delete_chat_use_case),
    request_meta: RequestMeta = Depends(get_request_meta),
):
    await use_case.execute(chat_id=chat_id, request_meta=request_meta, actor_id=actor_id)
    return {'message': 'ok'}