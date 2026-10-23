from app.infrastructure.events import EventRegistry
from app.domain.events.audit import AuditEvent
from app.domain.events.user import (
    UserCreated,
    UserUpdated,
    UserDeleted,
    UserPasswordChanged, UserUpdatedRole,
)
from app.domain.events.room import (
    RoomCreated,
    RoomUpdated,
    RoomDeleted
)
from app.domain.events.chat import (
    ChatMemberAdded,
    ChatMemberRemoved,
    ChatMemberRoleChanged,
    ChatOwnershipTransferred, ChatAdded, ChatInvalidate,
)
from app.domain.events.message import (
    MessageSent,
    MessageEdited,
    MessageDeleted
)
from app.infrastructure.mongo.analytics.repositories import ChatAnalyticsRepository, UserAnalyticsRepository, \
    RoomAnalyticsRepository, MessageAnalyticsRepository
from app.infrastructure.mongo.audit.repositories import AuditRepository
from app.infrastructure.redis import JWTWhiteListCache, UserCache, RoomCache, ChatMessageCache, ChatCache
from app.shared.event_handlers import (
    SaveAuditEventToMongo,
    SaveRoomMemberEvent,
    RemoveRoomMemberEvent,
    RoleChangeEvent,
    ChatOwnershipEvent,
    MessageSentEvent,
    MessageEditedEvent,
    MessageDeletedEvent,
    SaveRoomEvent,
    UpdateRoomEvent,
    DeleteRoomEvent,
    SaveRoomToCacheOnRoomCreated,
    InvalidateRoomCacheOnRoomUpdated,
    InvalidateRoomCacheOnRoomDeleted,
    SaveUserEvent,
    SaveUserToCacheOnUserCreated,
    UpdateUserEvent,
    InvalidateUserCacheOnUserUpdated,
    DeleteUserEvent,
    InvalidateUserCacheOnUserDeleted,
    RevokeAllTokensOnUserDeleted,
    ChangePswUserEvent,
    RevokeAllTokensOnUserPasswordChanged
)
from app.shared.event_handlers.chat import SaveNewChatInCache, InvalidateCacheInChat
from app.shared.event_handlers.user import RevokeAllTokensOnUserRoleChanged, InvalidateUserCacheChangePsw, \
    InvalidateUserCacheChangeRole


def register_event_handlers(
    registry: EventRegistry,
    audit_repo: AuditRepository,
    chat_repo: ChatAnalyticsRepository,
    msg_repo: MessageAnalyticsRepository,
    room_repo: RoomAnalyticsRepository,
    jwt_white_list: JWTWhiteListCache,
    user_repo: UserAnalyticsRepository,
    user_cache: UserCache,
    room_cache: RoomCache,
    chat_cache: ChatCache
):
    """Зарегистрировать все обработчики доменных событий."""

    # События сообщений
    registry.sub(MessageSent, MessageSentEvent(repo=msg_repo).handle)
    registry.sub(MessageEdited, MessageEditedEvent(repo=msg_repo).handle)
    registry.sub(MessageDeleted, MessageDeletedEvent(repo=msg_repo).handle)

    # События чатов
    registry.sub(ChatAdded, SaveNewChatInCache(cache=chat_cache).handle)
    registry.sub(ChatInvalidate, InvalidateCacheInChat(cache=chat_cache).handle)
    registry.sub(ChatMemberAdded, SaveRoomMemberEvent(repo=chat_repo).handle)
    registry.sub(ChatMemberRemoved, RemoveRoomMemberEvent(repo=chat_repo).handle)
    registry.sub(ChatMemberRoleChanged, RoleChangeEvent(repo=chat_repo).handle)
    registry.sub(ChatOwnershipTransferred, ChatOwnershipEvent(repo=chat_repo).handle)

    # События комнат
    registry.sub(RoomCreated, SaveRoomToCacheOnRoomCreated(cache=room_cache).handle)
    registry.sub(RoomCreated, SaveRoomEvent(repo=room_repo).handle)
    registry.sub(RoomUpdated, InvalidateRoomCacheOnRoomUpdated(cache=room_cache).handle)
    registry.sub(RoomUpdated, UpdateRoomEvent(repo=room_repo).handle)
    registry.sub(RoomDeleted, InvalidateRoomCacheOnRoomDeleted(cache=room_cache).handle)
    registry.sub(RoomDeleted, DeleteRoomEvent(repo=room_repo).handle)

    # События пользователей
    registry.sub(UserCreated, SaveUserToCacheOnUserCreated(cache=user_cache).handle)
    registry.sub(UserCreated, SaveUserEvent(repo=user_repo).handle)
    registry.sub(UserUpdated, InvalidateUserCacheOnUserUpdated(cache=user_cache).handle)
    registry.sub(UserUpdated, UpdateUserEvent(repo=user_repo).handle)
    registry.sub(UserDeleted, InvalidateUserCacheOnUserDeleted(cache=user_cache).handle)
    registry.sub(UserDeleted, DeleteUserEvent(repo=user_repo).handle)
    registry.sub(UserDeleted, RevokeAllTokensOnUserDeleted(jwt_white_list=jwt_white_list).handle)
    registry.sub(UserPasswordChanged, ChangePswUserEvent(repo=user_repo).handle)
    registry.sub(UserPasswordChanged, RevokeAllTokensOnUserPasswordChanged(jwt_white_list=jwt_white_list).handle)
    registry.sub(UserUpdatedRole, RevokeAllTokensOnUserRoleChanged(jwt_white_list=jwt_white_list).handle)
    registry.sub(UserPasswordChanged, InvalidateUserCacheChangePsw(cache=user_cache).handle)
    registry.sub(UserUpdatedRole, InvalidateUserCacheChangeRole(cache=user_cache).handle)

    # Аудит действий пользователя
    registry.sub(AuditEvent, SaveAuditEventToMongo(repo=audit_repo).handle)