from datetime import timedelta
from app.business_logic.email_sender import EmailSender
from app.business_logic.encrypte_manager import SymmetricEncode
from app.business_logic.jwt_manager import JWTAccessManager, JWTRefreshManager, JWTFacade
from app.business_logic.redis_adapter import (
    Cache,
    JWTWhiteListCache,
    SessionKeyStorage,
    VerifyCodeStorage,
    RedisConnection
)
from app.business_logic.websocket import UserConnectionManager, WSBroker
from app.data_layer.database import SQLDatabase, MongoticDatabase
from app.shared.config import BaseConfig


class Bootstrap:
    """Bootstrap для инициализации инфраструктуры"""
    def __init__(self, config: BaseConfig):
        self._redis_connection_manager = RedisConnection()
        self._redis_conn = None
        self.config = config
        self._cache = None
        self._jwt_white_list = None
        self._session_key_storage = None
        self._verify_code_storage = None
        self._ws_manager = None
        self._ws_broker = None
        self._smtp_service = None
        self._jwt_access_manager = None
        self._jwt_refresh_manage = None
        self._postgres_db = None
        self._mongo_db = None
        self._encrypt_manager = None
        self._jwt_facade = None

    async def _init_redis_conn(self):
        """Инициализации подключения к redis"""
        self._redis_conn = await self._redis_connection_manager.connection(self.config.redis.url)

    async def init_app(self):
        """Инициализация приложения"""
        await self._init_redis_conn()
        self._init_cache()
        self._init_jwt_white_list()
        self._init_session_key_storage()
        self._init_verify_code_storage()
        self._init_ws_manager()
        self._init_ws_broker()
        self._init_smtp_service()
        self._init_jwt_tokens()
        self._init_sql_database()
        self._init_mongodb_database()
        self._init_encrypt_manager()
        self._init_jwt_facade()

    def _init_jwt_facade(self):
        """Инициализация фасада для jwt токенов"""
        self._jwt_facade = JWTFacade

    def _init_cache(self):
        """Инициализация кеша"""
        self._cache = Cache(self._redis_conn)

    def _init_jwt_white_list(self):
        """Инициализация хранилища белых списков"""
        self._jwt_white_list = JWTWhiteListCache(self._redis_conn)

    def _init_session_key_storage(self):
        """Инициализация хранилища сессионных ключей"""
        self._session_key_storage = SessionKeyStorage(self._redis_conn)

    def _init_verify_code_storage(self):
        """Инициализация хранилища кодом подтверждения"""
        self._verify_code_storage = VerifyCodeStorage(self._redis_conn)

    def _init_ws_manager(self):
        """Инициализация брокера ws менеджера"""
        self._ws_manager = UserConnectionManager()

    def _init_ws_broker(self):
        """Инициализация брокера для передачи сообщений"""
        self._ws_broker = WSBroker(self._redis_conn, self._ws_manager)

    def _init_smtp_service(self):
        """Инициализация smtp сервиса"""
        self._smtp_service = EmailSender(
            smtp_server=self.config.smtp.server,
            port=self.config.smtp.port,
            sender_email=self.config.smtp.gmail,
            password=self.config.smtp.app_psw
        )

    def _init_jwt_tokens(self):
        """Инициализация jwt токенов"""
        JWTAccessManager.ALGORITHM = self.config.jwt_access.algorithm
        JWTAccessManager.EXPIRES_DELTA = timedelta(
            minutes=self.config.jwt_access.expiresdelta
        )
        JWTAccessManager.SECRET_KEY = self.config.jwt_access.secretkey

        JWTRefreshManager.ALGORITHM = self.config.jwt_refresh.algorithm
        JWTRefreshManager.EXPIRES_DELTA = timedelta(
            days=self.config.jwt_refresh.expiresdelta
        )
        JWTRefreshManager.SECRET_KEY = self.config.jwt_refresh.secretkey
        self._jwt_access_manager = JWTAccessManager
        self._jwt_refresh_manage = JWTRefreshManager

    def _init_sql_database(self):
        """Инициализация базы данных SQLAlchemy"""
        self._postgres_db = SQLDatabase(self.config.postgres.url)

    def _init_mongodb_database(self):
        """Инициализация базы данных Mongodb"""
        self._mongo_db = MongoticDatabase(self.config.mongodb.url)

    def _init_encrypt_manager(self):
        """Инициализация менеджера шифрования и дешифрования сообщений"""
        self._encrypt_manager = SymmetricEncode(app_key=self.config.app_key)

    @property
    def smtp_service(self):
        if not self._smtp_service:
            raise Exception
        return self._smtp_service

    @property
    def postgres_db(self) -> SQLDatabase:
        if not self._postgres_db:
            raise Exception
        return self._postgres_db

    @property
    def mongo_db(self) -> MongoticDatabase:
        if not self._mongo_db:
            raise Exception
        return self._mongo_db

    @property
    def cache(self) -> Cache:
        if not self._cache:
            raise Exception
        return self._cache

    @property
    def jwt_white_list(self) -> JWTWhiteListCache:
        if not self._jwt_white_list:
            raise Exception
        return self._jwt_white_list

    @property
    def jwt_facade(self) -> type[JWTFacade]:
        if not self._jwt_facade:
            raise Exception
        return self._jwt_facade

    @property
    def session_key_storage(self) -> SessionKeyStorage:
        if not self._session_key_storage:
            raise Exception
        return self._session_key_storage

    @property
    def verify_code_storage(self) -> VerifyCodeStorage:
        if not self._verify_code_storage:
            raise Exception
        return self._verify_code_storage

    @property
    def ws_manager(self) -> UserConnectionManager:
        if not self._ws_manager:
            raise Exception
        return self._ws_manager

    @property
    def ws_broker(self) -> WSBroker:
        if not self._ws_broker:
            raise Exception
        return self._ws_broker

    @property
    def jwt_access_manager(self) -> JWTAccessManager:
        if not self._jwt_access_manager:
            raise Exception
        return self._jwt_access_manager

    @property
    def jwt_refresh_manager(self) -> JWTRefreshManager:
        if not self._jwt_refresh_manage:
            raise Exception
        return self._jwt_refresh_manage

    @property
    def encrypt_manager(self) -> SymmetricEncode:
        if not self._encrypt_manager:
            raise Exception
        return self._encrypt_manager


bootstrap: Bootstrap | None = None


def get_bootstrap() -> Bootstrap:
    if not bootstrap:
        raise Exception
    return bootstrap


async def set_bootstrap(config: BaseConfig):
    global bootstrap
    bootstrap = Bootstrap(config)
    await bootstrap.init_app()
