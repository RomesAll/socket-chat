from fastapi import APIRouter, Depends
from app.business_logic.services.audit_service import AuditService
from app.di.auth import require_super_admins
from app.di.dependencies import get_audit_service
from app.domain.events.enums import ActionType


router = APIRouter(
    prefix="/audit",
    tags=["audit"],
    dependencies=[Depends(require_super_admins)]
)


@router.get("/actor/{actor_id}")
async def get_by_actor(
    actor_id: str,
    limit: int = 100,
    offset: int = 0,
    service: AuditService = Depends(get_audit_service),
):
    return await service.get_by_actor(actor_id, limit, offset)


@router.get("/target/{action}/{target_id}")
async def get_by_target(
    action: ActionType,
    target_id: str,
    limit: int = 100,
    offset: int = 0,
    service: AuditService = Depends(get_audit_service),
):
    return await service.get_by_target(action, target_id, limit, offset)


@router.get("/action/{action}")
async def get_by_action(
    action: ActionType,
    days: int = 30,
    limit: int = 1000,
    offset: int = 0,
    service: AuditService = Depends(get_audit_service),
):
    return await service.get_by_action(action, days, limit, offset)


@router.get("/request/{request_id}")
async def get_by_request_id(
    request_id: str,
    service: AuditService = Depends(get_audit_service),
):
    return await service.get_by_request_id(request_id)


@router.get("/actor-target")
async def get_by_actor_target(
    actor_id: str,
    target: str,
    days: int = 30,
    service: AuditService = Depends(get_audit_service),
):
    return await service.get_by_actor_target(actor_id, target, days)