from typing import AsyncIterator
from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.business_logic.mappers import UserMapper, ChatMapper, RoomMapper, MessageMapper
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
from app.infrastructure.redis.cache import (
    ChatCache,
    ChatMessageCache,
    UnreadCache,
    UserCache,
    RoomCache,
    PresenceCache
)
from app.infrastructure.events import EventRegistry
from app.infrastructure.mongo.audit.repositories import AuditRepository
from app.infrastructure.mongo.invite_tokens.repositories.invite_token_repo import InviteTokenRepository
from app.infrastructure.mongo.analytics.repositories import (
    UserAnalyticsRepository,
    ChatAnalyticsRepository,
    MessageAnalyticsRepository,
    RoomAnalyticsRepository,
)
from app.infrastructure.redis import (
    VerifyCodeStorage,
    JWTWhiteListCache,
    SessionKeyStorage,
)
from app.infrastructure.security import (
    PasswordManager,
    SymmetricEncode,
    JWTFacade, SecretsCodeGenerator,
)
from app.infrastructure.email import EmailSender
from app.infrastructure.websocket import UserConnectionManager, WSBroker


# Получение паттерна UOW

async def get_uow(request: Request) -> AsyncIterator[UnitOfWork]:
    """
    Создать UnitOfWork для запроса.

    Открывает сессию, отдаёт в Depends, коммитит/откатывает и закрывает
    после ответа. Публикует события после коммита.
    """
    session: AsyncSession = request.app.state.postgres.session()
    registry: EventRegistry = request.app.state.event_registry

    uow = UnitOfWork(session, registry)
    async with uow:
        yield uow


# Получение объектов redis


def get_chat_cache(request: Request) -> ChatCache:
    return request.app.state.chat_cache


def get_chat_message_cache(request: Request) -> ChatMessageCache:
    return request.app.state.chat_message_cache


def get_unread_cache(request: Request) -> UnreadCache:
    return request.app.state.unread_cache


def get_user_cache(request: Request) -> UserCache:
    return request.app.state.user_cache


def get_room_cache(request: Request) -> RoomCache:
    return request.app.state.room_cache


def get_presence_cache(request: Request) -> PresenceCache:
    return request.app.state.presence_cache


def get_jwt_white_list(request: Request) -> JWTWhiteListCache:
    return request.app.state.jwt_white_list


def get_session_key_storage(request: Request) -> SessionKeyStorage:
    return request.app.state.session_key_storage


def get_verify_code_storage(request: Request) -> VerifyCodeStorage:
    return request.app.state.verify_code_storage


# Получение сторонних сервисов


def get_event_registry(request: Request) -> EventRegistry:
    return request.app.state.event_registry


def get_psw_manager(request: Request) -> PasswordManager:
    return request.app.state.psw_manager


def get_cipher(request: Request) -> SymmetricEncode:
    return request.app.state.cipher


def get_jwt_facade(request: Request) -> type[JWTFacade]:
    return request.app.state.jwt_facade


def get_email_sender(request: Request) -> EmailSender:
    return request.app.state.email_sender


def get_ws_manager(request: Request) -> UserConnectionManager:
    return request.app.state.ws_manager


def get_ws_broker(request: Request) -> WSBroker:
    return request.app.state.ws_broker


# Получение репозиториев mongo


def get_user_analytics_repo(request: Request) -> UserAnalyticsRepository:
    return request.app.state.user_analytics_repo


def get_chat_analytics_repo(request: Request) -> ChatAnalyticsRepository:
    return request.app.state.chat_analytics_repo


def get_message_analytics_repo(request: Request) -> MessageAnalyticsRepository:
    return request.app.state.message_analytics_repo


def get_room_analytics_repo(request: Request) -> RoomAnalyticsRepository:
    return request.app.state.room_analytics_repo


def get_audit_repo(request: Request) -> AuditRepository:
    return request.app.state.audit_repo


def get_invite_token_repo(request: Request) -> InviteTokenRepository:
    return request.app.state.invite_token_repo


# Получение сервисов


def get_user_service(
    uow: UnitOfWork = Depends(get_uow),
    user_cache: UserCache = Depends(get_user_cache),
    psw_manager: type[PasswordManager] = Depends(get_psw_manager)
) -> UserService:
    return UserService(uow=uow, mapper=UserMapper(), cache=user_cache, psw_manager=psw_manager)


def get_chat_service(
    uow: UnitOfWork = Depends(get_uow),
    chat_cache: ChatCache = Depends(get_chat_cache),
) -> ChatService:
    return ChatService(uow=uow, mapper=ChatMapper(), cache=chat_cache)


def get_room_service(
    uow: UnitOfWork = Depends(get_uow),
    room_cache: RoomCache = Depends(get_room_cache),
) -> RoomService:
    return RoomService(uow=uow, mapper=RoomMapper(), cache=room_cache)


def get_message_service(
    uow: UnitOfWork = Depends(get_uow),
    msg_cache: ChatMessageCache = Depends(get_room_cache),
) -> MessageService:
    return MessageService(uow=uow, mapper=MessageMapper(), cache=msg_cache)


def get_verification_service(
    storage: VerifyCodeStorage = Depends(get_verify_code_storage),
) -> VerificationService:
    return VerificationService(storage=storage, generator=SecretsCodeGenerator())


def get_token_service(
    white_list: JWTWhiteListCache = Depends(get_jwt_white_list),
    jwt_facade: type[JWTFacade] = Depends(get_jwt_facade),
) -> TokenService:
    return TokenService(jwt_white_list=white_list, jwt_facade=jwt_facade)


def get_invite_token_service(
    repo: InviteTokenRepository = Depends(get_invite_token_repo),
) -> InviteTokenService:
    return InviteTokenService(repo=repo)