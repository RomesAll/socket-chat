from uuid import UUID
from fastapi import APIRouter, Depends
from app.business_logic.services import (
    ChatReportService,
    MessageReportService,
    RoomReportService,
    UserReportService
)
from app.di.auth import require_admins
from app.di.dependencies import (
    get_chat_report_service,
    get_msg_report_service,
    get_room_report_service,
    get_user_report_service
)

router = APIRouter(prefix='/reports', tags=['reports'], dependencies=[Depends(require_admins)])


@router.get('/chats/{chat_id}')
async def get_chats_report(
    chat_id: UUID,
    days: int = 30,
    service: ChatReportService = Depends(get_chat_report_service)
):
    user_added = await service.get_added_member(chat_id, days)
    user_removed = await service.get_removed_member(chat_id, days)
    change_owner = await service.get_changed_owner(chat_id)
    return {
        'user_added': user_added,
        'user_removed': user_removed,
        'change_owner': change_owner
    }


@router.get('/messages/count-send')
async def get_msg_report(
    days: int = 30,
    service: MessageReportService = Depends(get_msg_report_service)
):
    msg_count = await service.get_count_msg_by_days(days)
    return msg_count


@router.get('/messages/count-send/{chat_id}')
async def get_msg_by_chat_report(
    chat_id: UUID,
    days: int = 30,
    service: MessageReportService = Depends(get_msg_report_service)
):
    msg_count = await service.get_count_chat_msg_by_days(chat_id, days)
    return msg_count


@router.get('/messages/top-chats')
async def get_top_chats(
    limit: int = 10,
    service: MessageReportService = Depends(get_msg_report_service)
):
    msg_count = await service.get_top_chat(limit)
    return msg_count


@router.get('/messages/top-senders')
async def get_top_senders(
    limit: int = 10,
    service: MessageReportService = Depends(get_msg_report_service)
):
    msg_count = await service.get_top_senders(limit)
    return msg_count


@router.get('/rooms')
async def get_rooms_report(
    days: int = 30,
    service: RoomReportService = Depends(get_room_report_service)
):
    created_room = await service.get_count_created_by_day(days)
    deleted_room = await service.get_count_deleted_by_day(days)
    return {
        'created_room': created_room,
        'deleted_room': deleted_room
    }


@router.get('/rooms/top-rooms')
async def get_top_rooms(
    top_count: int = 5,
    service: RoomReportService = Depends(get_room_report_service)
):
    top_rooms = await service.top_rooms_by_member(top_count)
    return top_rooms


@router.get('/users')
async def get_users_report(
    days: int = 30,
    service: UserReportService = Depends(get_user_report_service)
):
    created_users = await service.get_count_created_by_day(days)
    deleted_users = await service.get_count_deleted_by_day(days)
    count_admin = await service.get_count_admin()
    count_users = await service.get_count_user()
    top_domain_email = await service.get_top_email_domain()
    return {
        'created_users': created_users,
        'deleted_users': deleted_users,
        'count_admin': count_admin,
        'count_users': count_users,
        'top_domain_email': top_domain_email
    }