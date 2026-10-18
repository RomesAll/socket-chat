from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.infrastructure.database.session import PostgresClient
from app.infrastructure.email import EmailSender
from app.infrastructure.mongo.analytics.repositories import UserAnalyticsRepository, MessageAnalyticsRepository, \
    ChatAnalyticsRepository, RoomAnalyticsRepository
from app.infrastructure.mongo.audit.repositories import AuditRepository
from app.infrastructure.mongo.client import MongoClient
from app.infrastructure.redis import RedisClient, JWTWhiteListCache, SessionKeyStorage, VerifyCodeStorage, ChatCache, \
    ChatMessageCache, UnreadCache, UserCache, RoomCache, PresenceCache
from app.infrastructure.security import SecretsCodeGenerator, SymmetricEncode, JWTFacade, PasswordManager
from app.infrastructure.storage import FileManager
from app.infrastructure.websocket import WSBroker, UserConnectionManager
from app.shared.config import get_config
from app.di.events import register_event_handlers
from app.infrastructure.events import EventRegistry


@asynccontextmanager
async def lifespan(app: FastAPI):
    print('')
    config = get_config()
    app.state.config = config

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
    app.state.encrypt_manager = SymmetricEncode(app_key=config.app_token)
    app.state.jwt_facade_manager = JWTFacade
    app.state.psw_manager = PasswordManager
    app.state.file_manager = FileManager
    app.state.ws_manager = UserConnectionManager()
    app.state.ws_broker = WSBroker(
        redis_client=app.state.redis.client,
        manager=app.state.ws_manager
    )
    await app.state.ws_broker.start()

    db_redis = app.state.redis.client
    app.state.jwt_white_list = JWTWhiteListCache(db_redis)
    app.state.session_key_storage = SessionKeyStorage(db_redis)
    app.state.verify_code_storage = VerifyCodeStorage(db_redis)
    app.state.chat_cache = ChatCache(db_redis)
    app.state.chat_message_cache = ChatMessageCache(db_redis)
    app.state.unread_cache = UnreadCache(db_redis)
    app.state.user_cache = UserCache(db_redis)
    app.state.room_cache = RoomCache(db_redis)
    app.state.presence_cache = PresenceCache(db_redis)

    db = app.state.mongo.db
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
        chat_msg_cache=app.state.chat_message_cache
    )

    yield

    await app.state.postgres.close()
    await app.state.redis.close()
    await app.state.mongo.close()