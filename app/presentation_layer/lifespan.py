from contextlib import asynccontextmanager
from datetime import timedelta
from fastapi import FastAPI
from app.infrastructure.database.session import PostgresClient
from app.infrastructure.email import EmailSender
from app.infrastructure.mongo.analytics.repositories import UserAnalyticsRepository, MessageAnalyticsRepository, \
    ChatAnalyticsRepository, RoomAnalyticsRepository
from app.infrastructure.mongo.audit.repositories import AuditRepository
from app.infrastructure.mongo.client import MongoClient
from app.infrastructure.mongo.invite_tokens.repositories import InviteTokenRepository
from app.infrastructure.redis import RedisClient, JWTWhiteListCache, SessionKeyStorage, VerifyCodeStorage, ChatCache, \
    ChatMessageCache, UnreadCache, UserCache, RoomCache, PresenceCache
from app.infrastructure.security import SecretsCodeGenerator, SymmetricEncode, JWTFacade, PasswordManager, \
    JWTAccessManager, JWTRefreshManager
from app.infrastructure.storage import AsyncFileAdapter
from app.infrastructure.websocket import WSBroker, UserConnectionManager
from app.presentation_layer.rest_api.routers import api_register
from app.shared.config import get_config
from app.di.events import register_event_handlers
from app.infrastructure.events import EventRegistry


@asynccontextmanager
async def lifespan(app: FastAPI):
    config = get_config()
    app.state.config = config

    jwt_access_manager = JWTAccessManager(
        secret_key=config.jwt_access.secretkey,
        alg=config.jwt_access.algorithm,
        expires_delta=timedelta(seconds=config.jwt_access.expiresdelta)
    )

    jwt_refresh_manager = JWTRefreshManager(
        secret_key=config.jwt_refresh.secretkey,
        alg=config.jwt_refresh.algorithm,
        expires_delta=timedelta(seconds=config.jwt_refresh.expiresdelta)
    )

    # Объекты singleton
    app.state.postgres = PostgresClient(config.postgres.url, echo=True)
    app.state.email_sender = EmailSender(
        smtp_server=config.smtp.server,
        port=config.smtp.port,
        sender_email=config.smtp.gmail,
        password=config.smtp.app_psw
    )
    app.state.event_registry = EventRegistry()
    app.state.mongo = MongoClient(
        url=config.mongodb.url,
        db_name=config.mongodb.db
    )
    app.state.redis = RedisClient(uri=config.redis.url)
    app.state.code_generator = SecretsCodeGenerator()
    app.state.cipher = SymmetricEncode(app_key=config.app_token)
    app.state.jwt_facade = JWTFacade(jwt_access_manager, jwt_refresh_manager)
    app.state.psw_manager = PasswordManager
    app.state.file_manager = AsyncFileAdapter()
    app.state.ws_manager = UserConnectionManager()
    app.state.ws_broker = WSBroker(
        redis_client=app.state.redis.client,
        manager=app.state.ws_manager
    )
    await app.state.ws_broker.start()

    db_redis = app.state.redis.client
    app.state.jwt_white_list = JWTWhiteListCache(db_redis)
    app.state.session_key_storage = SessionKeyStorage(db_redis)
    app.state.verify_code_storage = VerifyCodeStorage(db_redis, ttl=config.cache.verify_code)
    app.state.chat_cache = ChatCache(db_redis, ttl=config.cache.chat)
    app.state.chat_message_cache = ChatMessageCache(db_redis, ttl=60)
    app.state.unread_cache = UnreadCache(db_redis)
    app.state.user_cache = UserCache(db_redis, ttl=config.cache.user)
    app.state.room_cache = RoomCache(db_redis, ttl=config.cache.room)
    app.state.presence_cache = PresenceCache(db_redis, ttl=config.cache.presence)

    db = app.state.mongo.db
    app.state.invite_token_repo = InviteTokenRepository(db)
    app.state.user_analytics_repo = UserAnalyticsRepository(db)
    app.state.message_analytics_repo = MessageAnalyticsRepository(db)
    app.state.audit_repo = AuditRepository(db)
    app.state.chat_analytics_repo = ChatAnalyticsRepository(db)
    app.state.room_analytics_repo = RoomAnalyticsRepository(db)

    # Регистрация доменных событий
    register_event_handlers(
        registry=app.state.event_registry,
        audit_repo=app.state.audit_repo,
        chat_repo=app.state.chat_analytics_repo,
        msg_repo=app.state.message_analytics_repo,
        room_repo=app.state.room_analytics_repo,
        jwt_white_list=app.state.jwt_white_list,
        user_repo=app.state.user_analytics_repo,
        user_cache=app.state.user_cache,
        room_cache=app.state.room_cache,
        chat_cache=app.state.chat_cache
    )

    api_register(app=app)

    yield

    await app.state.postgres.close()
    await app.state.redis.close()
    await app.state.mongo.close()