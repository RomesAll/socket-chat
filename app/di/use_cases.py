from fastapi import Depends

from app.business_logic.unit_of_work import UnitOfWork
from app.business_logic.services import (
    UserService,
    ChatService,
    RoomService,
    MessageService,
    VerificationService,
    TokenService,
    InviteTokenService,
)
from app.business_logic.use_cases.auth import (
    LoginWithSendCodeUseCase,
    LoginWithoutSendCodeUseCase,
    VerifyCodeUseCase,
    RefreshTokenUseCase,
    LogoutUseCase,
    LogoutAllUseCase,
)
from app.business_logic.use_cases.user import (
    UpdateUserUseCase,
    DeleteUserUseCase,
    ChangeUserRoleUseCase,
    ChangeUserPasswordUseCase,
    RegisterUserUseCase,
    GetUserBriefInfoUseCase,
)
from app.business_logic.use_cases.room import (
    CreateRoomUseCase,
    UpdateRoomUseCase,
    DeleteRoomUseCase,
)
from app.business_logic.use_cases.chat import (
    JoinByInviteUseCase,
    GenerateInviteLinkUseCase,
    RemoveChatMemberUseCase,
    ChangeChatMemberRoleUseCase,
    TransferChatOwnershipUseCase,
)
from app.business_logic.use_cases.message import (
    SendMessageUseCase,
    DeleteMessageUseCase,
    GetChatHistoryUseCase,
    MarkMessagesReadUseCase,
)
from app.business_logic.use_cases.ws import (
    ConnectWebSocketUseCase,
    DisconnectWebSocketUseCase,
)
from app.di.dependencies import (
    get_uow,
    get_user_service,
    get_chat_service,
    get_room_service,
    get_message_service,
    get_verification_service,
    get_token_service,
    get_invite_token_service,
    get_unread_cache,
    get_presence_cache,
    get_email_sender,
    get_cipher,
    get_ws_broker,
    get_ws_manager,
    get_session_key_storage,
    get_user_analytics_repo,
    get_message_analytics_repo,
)
from app.infrastructure.security import SymmetricEncode


# auth use-cases

def get_register_user_use_case(
    user_service: UserService = Depends(get_user_service),
    verification_service: VerificationService = Depends(get_verification_service),
    email_sender=Depends(get_email_sender),
    uow: UnitOfWork = Depends(get_uow),
) -> RegisterUserUseCase:
    return RegisterUserUseCase(
        user_service=user_service,
        verification_service=verification_service,
        email_sender=email_sender,
        uow=uow,
    )


def get_login_with_send_code_use_case(
    user_service: UserService = Depends(get_user_service),
    verification_service: VerificationService = Depends(get_verification_service),
    email_sender=Depends(get_email_sender),
    uow: UnitOfWork = Depends(get_uow),
) -> LoginWithSendCodeUseCase:
    return LoginWithSendCodeUseCase(
        user_service=user_service,
        verification_service=verification_service,
        email_sender=email_sender,
        uow=uow,
    )


def get_login_without_send_code_use_case(
    user_service: UserService = Depends(get_user_service),
    verification_service: VerificationService = Depends(get_verification_service),
    uow: UnitOfWork = Depends(get_uow),
) -> LoginWithoutSendCodeUseCase:
    return LoginWithoutSendCodeUseCase(
        user_service=user_service,
        verification_service=verification_service,
        uow=uow,
    )


def get_verify_code_use_case(
    user_service: UserService = Depends(get_user_service),
    verification_service: VerificationService = Depends(get_verification_service),
    token_service: TokenService = Depends(get_token_service),
    uow: UnitOfWork = Depends(get_uow),
) -> VerifyCodeUseCase:
    return VerifyCodeUseCase(
        user_service=user_service,
        verification_service=verification_service,
        token_service=token_service,
        uow=uow,
    )


def get_refresh_token_use_case(
    user_service: UserService = Depends(get_user_service),
    token_service: TokenService = Depends(get_token_service),
    uow: UnitOfWork = Depends(get_uow),
) -> RefreshTokenUseCase:
    return RefreshTokenUseCase(
        user_service=user_service,
        token_service=token_service,
        uow=uow,
    )


def get_logout_use_case(
    token_service: TokenService = Depends(get_token_service),
    uow: UnitOfWork = Depends(get_uow),
) -> LogoutUseCase:
    return LogoutUseCase(token_service=token_service, uow=uow)


def get_logout_all_use_case(
    token_service: TokenService = Depends(get_token_service),
    uow: UnitOfWork = Depends(get_uow),
) -> LogoutAllUseCase:
    return LogoutAllUseCase(token_service=token_service, uow=uow)


# user use-cases


def get_update_user_use_case(
    user_service: UserService = Depends(get_user_service),
    uow: UnitOfWork = Depends(get_uow),
) -> UpdateUserUseCase:
    return UpdateUserUseCase(user_service=user_service, uow=uow)


def get_delete_user_use_case(
    user_service: UserService = Depends(get_user_service),
    chat_service: ChatService = Depends(get_chat_service),
    room_service: RoomService = Depends(get_room_service),
    uow: UnitOfWork = Depends(get_uow),
) -> DeleteUserUseCase:
    return DeleteUserUseCase(
        user_service=user_service,
        chat_service=chat_service,
        room_service=room_service,
        uow=uow,
    )


def get_change_user_role_use_case(
    user_service: UserService = Depends(get_user_service),
    uow: UnitOfWork = Depends(get_uow),
    token_service: TokenService = Depends(get_token_service)
) -> ChangeUserRoleUseCase:
    return ChangeUserRoleUseCase(user_service=user_service, uow=uow, token_service=token_service)


def get_change_user_password_use_case(
    user_service: UserService = Depends(get_user_service),
    token_service: TokenService = Depends(get_token_service),
    uow: UnitOfWork = Depends(get_uow),
) -> ChangeUserPasswordUseCase:
    return ChangeUserPasswordUseCase(
        user_service=user_service,
        token_service=token_service,
        uow=uow,
    )


def get_user_profile_use_case(
    user_service: UserService = Depends(get_user_service),
    presence=Depends(get_presence_cache),
) -> GetUserBriefInfoUseCase:
    return GetUserBriefInfoUseCase(
        user_service=user_service,
        presence_cache=presence,
    )


# room use-cases

def get_create_room_use_case(
    chat_service: ChatService = Depends(get_chat_service),
    room_service: RoomService = Depends(get_room_service),
    uow: UnitOfWork = Depends(get_uow),
) -> CreateRoomUseCase:
    return CreateRoomUseCase(
        chat_service=chat_service,
        room_service=room_service,
        uow=uow,
    )


def get_update_room_use_case(
    chat_service: ChatService = Depends(get_chat_service),
    room_service: RoomService = Depends(get_room_service),
    uow: UnitOfWork = Depends(get_uow),
) -> UpdateRoomUseCase:
    return UpdateRoomUseCase(
        chat_service=chat_service,
        room_service=room_service,
        uow=uow,
    )


def get_delete_room_use_case(
    chat_service: ChatService = Depends(get_chat_service),
    room_service: RoomService = Depends(get_room_service),
    uow: UnitOfWork = Depends(get_uow),
) -> DeleteRoomUseCase:
    return DeleteRoomUseCase(
        chat_service=chat_service,
        room_service=room_service,
        uow=uow,
    )


def get_generate_invite_link_use_case(
    chat_service: ChatService = Depends(get_chat_service),
    invite_service: InviteTokenService = Depends(get_invite_token_service),
    uow: UnitOfWork = Depends(get_uow),
) -> GenerateInviteLinkUseCase:
    return GenerateInviteLinkUseCase(
        chat_service=chat_service,
        invite_service=invite_service,
        uow=uow,
    )


def get_join_by_invite_use_case(
    chat_service: ChatService = Depends(get_chat_service),
    room_service: RoomService = Depends(get_room_service),
    invite_service: InviteTokenService = Depends(get_invite_token_service),
    uow: UnitOfWork = Depends(get_uow),
) -> JoinByInviteUseCase:
    return JoinByInviteUseCase(
        chat_service=chat_service,
        room_service=room_service,
        invite_service=invite_service,
        uow=uow,
    )


# chat use-cases


def get_join_invite_use_case(
    chat_service: ChatService = Depends(get_chat_service),
    room_service: RoomService = Depends(get_room_service),
    invite_service: InviteTokenService = Depends(get_invite_token_service),
    uow: UnitOfWork = Depends(get_uow),
) -> JoinByInviteUseCase:
    return JoinByInviteUseCase(
        chat_service=chat_service,
        room_service=room_service,
        uow=uow,
        invite_service=invite_service
    )


def get_generate_invite_use_case(
    chat_service: ChatService = Depends(get_chat_service),
    invite_service: InviteTokenService = Depends(get_invite_token_service),
    uow: UnitOfWork = Depends(get_uow),
) -> GenerateInviteLinkUseCase:
    return GenerateInviteLinkUseCase(
        chat_service=chat_service,
        uow=uow,
        invite_service=invite_service
    )


def get_remove_chat_member_use_case(
    chat_service: ChatService = Depends(get_chat_service),
    uow: UnitOfWork = Depends(get_uow),
) -> RemoveChatMemberUseCase:
    return RemoveChatMemberUseCase(chat_service=chat_service, uow=uow)


def get_change_chat_member_role_use_case(
    chat_service: ChatService = Depends(get_chat_service),
    uow: UnitOfWork = Depends(get_uow),
    room_service: RoomService = Depends(get_room_service)
) -> ChangeChatMemberRoleUseCase:
    return ChangeChatMemberRoleUseCase(chat_service=chat_service, uow=uow, room_service=room_service)


def get_transfer_chat_ownership_use_case(
    chat_service: ChatService = Depends(get_chat_service),
    uow: UnitOfWork = Depends(get_uow),
    room_service: RoomService = Depends(get_room_service)
) -> TransferChatOwnershipUseCase:
    return TransferChatOwnershipUseCase(chat_service=chat_service, uow=uow, room_service=room_service)


# message use-cases

def get_send_message_use_case(
    message_service: MessageService = Depends(get_message_service),
    chat_service: ChatService = Depends(get_chat_service),
    unread=Depends(get_unread_cache),
    ws_broker=Depends(get_ws_broker),
    uow: UnitOfWork = Depends(get_uow),
    encoder: SymmetricEncode = Depends(get_cipher)
) -> SendMessageUseCase:
    return SendMessageUseCase(
        message_service=message_service,
        chat_service=chat_service,
        unread_cache=unread,
        ws_broker=ws_broker,
        uow=uow,
        encoder=encoder
    )


def get_delete_message_use_case(
    message_service: MessageService = Depends(get_message_service),
    chat_service: ChatService = Depends(get_chat_service),
    ws_broker=Depends(get_ws_broker),
    uow: UnitOfWork = Depends(get_uow),
) -> DeleteMessageUseCase:
    return DeleteMessageUseCase(
        message_service=message_service,
        chat_service=chat_service,
        ws_broker=ws_broker,
        uow=uow,
    )


def get_chat_history_use_case(
    chat_service: ChatService = Depends(get_chat_service),
    message_service: MessageService = Depends(get_message_service),
    cipher=Depends(get_cipher),
) -> GetChatHistoryUseCase:
    return GetChatHistoryUseCase(
        chat_service=chat_service,
        message_service=message_service,
        cipher=cipher,
    )


def get_mark_messages_read_use_case(
    chat_service: ChatService = Depends(get_chat_service),
    message_service: MessageService = Depends(get_message_service),
    unread=Depends(get_unread_cache),
    ws_broker=Depends(get_ws_broker),
    uow: UnitOfWork = Depends(get_uow),
) -> MarkMessagesReadUseCase:
    return MarkMessagesReadUseCase(
        chat_service=chat_service,
        message_service=message_service,
        unread_cache=unread,
        ws_broker=ws_broker,
        uow=uow,
    )


# websocket use-cases

def get_connect_ws_use_case(
    user_service: UserService = Depends(get_user_service),
    chat_service: ChatService = Depends(get_chat_service),
    session_storage=Depends(get_session_key_storage),
    manager=Depends(get_ws_manager),
    ws_broker=Depends(get_ws_broker),
    presence=Depends(get_presence_cache),
) -> ConnectWebSocketUseCase:
    return ConnectWebSocketUseCase(
        user_service=user_service,
        chat_service=chat_service,
        session_storage=session_storage,
        manager=manager,
        ws_broker=ws_broker,
        presence=presence,
    )


def get_disconnect_ws_use_case(
    chat_service: ChatService = Depends(get_chat_service),
    session_storage=Depends(get_session_key_storage),
    manager=Depends(get_ws_manager),
    ws_broker=Depends(get_ws_broker),
    presence=Depends(get_presence_cache),
) -> DisconnectWebSocketUseCase:
    return DisconnectWebSocketUseCase(
        chat_service=chat_service,
        session_storage=session_storage,
        manager=manager,
        ws_broker=ws_broker,
        presence=presence,
    )