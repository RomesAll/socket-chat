from typing import AsyncIterator
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import HTTPConnection
from app.business_logic.mappers import UserMapper, ChatMapper, RoomMapper, MessageMapper
from app.business_logic.services.audit_service import AuditService
from app.business_logic.services.presence_service import PresenceService
from app.business_logic.unit_of_work import UnitOfWork
from app.business_logic.services import (
    UserService,
    ChatService,
    RoomService,
    MessageService,
    VerificationService,
    TokenService,
    InviteTokenService, ChatReportService, MessageReportService, RoomReportService, UserReportService,
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
from app.infrastructure.storage.file_manager import AsyncFileAdapter
from app.infrastructure.websocket import UserConnectionManager, WSBroker
from app.shared.config import BaseConfig


# Получение паттерна UOW

async def get_uow(connection: HTTPConnection) -> AsyncIterator[UnitOfWork]:
    """
    Создать UnitOfWork для запроса.

    Открывает сессию, отдаёт в Depends, коммитит/откатывает и закрывает
    после ответа. Публикует события после коммита.
    """
    session: AsyncSession = connection.app.state.postgres.session()
    registry: EventRegistry = connection.app.state.event_registry
    uow = UnitOfWork(session, registry)
    async with uow:
        yield uow


# Получение объектов redis


def get_chat_cache(connection: HTTPConnection) -> ChatCache:
    return connection.app.state.chat_cache


def get_chat_message_cache(connection: HTTPConnection) -> ChatMessageCache:
    return connection.app.state.chat_message_cache


def get_unread_cache(connection: HTTPConnection) -> UnreadCache:
    return connection.app.state.unread_cache


def get_user_cache(connection: HTTPConnection) -> UserCache:
    return connection.app.state.user_cache


def get_room_cache(connection: HTTPConnection) -> RoomCache:
    return connection.app.state.room_cache


def get_presence_cache(connection: HTTPConnection) -> PresenceCache:
    return connection.app.state.presence_cache


def get_jwt_white_list(connection: HTTPConnection) -> JWTWhiteListCache:
    return connection.app.state.jwt_white_list


def get_session_key_storage(connection: HTTPConnection) -> SessionKeyStorage:
    return connection.app.state.session_key_storage


def get_verify_code_storage(connection: HTTPConnection) -> VerifyCodeStorage:
    return connection.app.state.verify_code_storage


# Получение сторонних сервисов


def get_event_registry(connection: HTTPConnection) -> EventRegistry:
    return connection.app.state.event_registry


def get_psw_manager(connection: HTTPConnection) -> PasswordManager:
    return connection.app.state.psw_manager


def get_cipher(connection: HTTPConnection) -> SymmetricEncode:
    return connection.app.state.cipher


def get_jwt_facade(connection: HTTPConnection) -> JWTFacade:
    return connection.app.state.jwt_facade


def get_email_sender(connection: HTTPConnection) -> EmailSender:
    return connection.app.state.email_sender


def get_ws_manager(connection: HTTPConnection) -> UserConnectionManager:
    return connection.app.state.ws_manager


def get_ws_broker(connection: HTTPConnection) -> WSBroker:
    return connection.app.state.ws_broker


# Получение репозиториев mongo


def get_user_analytics_repo(connection: HTTPConnection) -> UserAnalyticsRepository:
    return connection.app.state.user_analytics_repo


def get_chat_analytics_repo(connection: HTTPConnection) -> ChatAnalyticsRepository:
    return connection.app.state.chat_analytics_repo


def get_message_analytics_repo(connection: HTTPConnection) -> MessageAnalyticsRepository:
    return connection.app.state.message_analytics_repo


def get_room_analytics_repo(connection: HTTPConnection) -> RoomAnalyticsRepository:
    return connection.app.state.room_analytics_repo


def get_audit_repo(connection: HTTPConnection) -> AuditRepository:
    return connection.app.state.audit_repo


def get_invite_token_repo(connection: HTTPConnection) -> InviteTokenRepository:
    return connection.app.state.invite_token_repo


def get_file_manager(connection: HTTPConnection) -> AsyncFileAdapter:
    return connection.app.state.file_manager


def get_state_config(connection: HTTPConnection) -> BaseConfig:
    return connection.app.state.config


# Получение сервисов

def get_audit_service(
    repo: AuditRepository = Depends(get_audit_repo)
):
    return AuditService(repo)


def get_presence_service(
    cache: PresenceCache = Depends(get_presence_cache),
    conn_manager: UserConnectionManager = Depends(get_ws_manager)
) -> PresenceService:
    return PresenceService(cache, conn_manager)


def get_chat_report_service(
    repo: ChatAnalyticsRepository = Depends(get_chat_analytics_repo)
) -> ChatReportService:
    return ChatReportService(repo)


def get_msg_report_service(
    repo: MessageAnalyticsRepository = Depends(get_message_analytics_repo)
) -> MessageReportService:
    return MessageReportService(repo)


def get_room_report_service(
    repo: RoomAnalyticsRepository = Depends(get_room_analytics_repo),
    uow: UnitOfWork = Depends(get_uow),
) -> RoomReportService:
    return RoomReportService(repo, uow.room_read_repo)


def get_user_report_service(
    repo: UserAnalyticsRepository = Depends(get_user_analytics_repo),
    uow: UnitOfWork = Depends(get_uow),
) -> UserReportService:
    return UserReportService(repo, uow.user_repo)


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
    msg_cache: ChatMessageCache = Depends(get_chat_message_cache),
) -> MessageService:
    return MessageService(uow=uow, mapper=MessageMapper(), cache=msg_cache)


def get_verification_service(
    storage: VerifyCodeStorage = Depends(get_verify_code_storage),
) -> VerificationService:
    return VerificationService(storage=storage, generator=SecretsCodeGenerator())


def get_token_service(
    white_list: JWTWhiteListCache = Depends(get_jwt_white_list),
    jwt_facade: JWTFacade = Depends(get_jwt_facade),
) -> TokenService:
    return TokenService(jwt_white_list=white_list, jwt_facade=jwt_facade)


def get_invite_token_service(
    repo: InviteTokenRepository = Depends(get_invite_token_repo),
) -> InviteTokenService:
    return InviteTokenService(repo=repo)