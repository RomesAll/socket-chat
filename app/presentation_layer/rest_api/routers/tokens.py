from uuid import UUID
from fastapi import APIRouter, Depends
from app.business_logic.services import TokenService
from app.business_logic.use_cases.auth.revoke_all_user_tokens import RevokeAllUserTokens
from app.di.dependencies import get_token_service
from app.di.auth import require_admins, get_user_id
from app.di.use_cases import get_revoke_user_tokens

router = APIRouter(prefix="/tokens", tags=["tokens"], dependencies=[Depends(require_admins)])


@router.delete("/{user_id}/all")
async def revoke_all_user_tokens(
        user_id: str,
        actor_id: str = Depends(get_user_id),
        use_case: RevokeAllUserTokens = Depends(get_revoke_user_tokens)
):
    await use_case.execute(user_id, actor_id)
    return {"status": "ok", "message": f"Все токены пользователя {user_id} отозваны"}


@router.delete("/{user_id}/{refresh_id}")
async def revoke_user_token(
        user_id: str,
        refresh_id: UUID,
        service: TokenService = Depends(get_token_service),
):
    await service.revoke(user_id, refresh_id)
    return {"status": "ok", "message": f"Токен {refresh_id} отозван"}