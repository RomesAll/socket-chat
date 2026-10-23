from fastapi import APIRouter, Depends
from app.business_logic.use_cases.chat.get_group_chats import GetGroupChatsUseCase
from app.business_logic.use_cases.chat.get_private_chats import GetPrivateChatsUseCase
from app.di.auth import get_user_id
from app.di.use_cases import get_private_chats_use_case, get_group_chats_use_case

router = APIRouter(prefix="/chats", tags=["chats"])


@router.get("/private/me")
async def get_my_private_chats(
    user_id: str = Depends(get_user_id),
    use_case: GetPrivateChatsUseCase = Depends(get_private_chats_use_case)
):
    return await use_case.execute(user_id)


@router.get("/group/me")
async def get_my_group_chats(
    user_id: str = Depends(get_user_id),
    use_case: GetGroupChatsUseCase = Depends(get_group_chats_use_case)
):
    return await use_case.execute(user_id)



