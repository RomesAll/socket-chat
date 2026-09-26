from enum import Enum
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import BaseModel, SecretStr, field_validator
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent.parent.resolve()


class AppMode(str, Enum):
    """Enum перечисление режимов работы программы"""
    DEV = 'dev'
    TEST = 'test'
    PROD = 'prod'


class PostgresqlSettings(BaseModel):
    """Конфиг для сервиса postgresql"""
    host: str
    port: int
    db: str
    user: str
    password: SecretStr

    @property
    def url(self):
        return (f'postgresql+psycopg://{self.user}:{self.password.get_secret_value()}'
                f'@{self.host}:{self.port}/{self.db}')


class RedisSettings(BaseModel):
    """Конфиг для сервиса redis"""
    host: str
    port: int
    db: int
    password: SecretStr

    @property
    def url(self):
        return (f'redis://:{self.password.get_secret_value()}'
                f'@{self.host}:{self.port}/{self.db}')


class JWTSettings(BaseModel):
    """Базовый конфиг для jwt auth"""
    algorithm: str
    expiresdelta: int
    secretkey: str


class LogLevelInfo(BaseModel):
    """Конфиг для хранения уровня логирования"""
    log_name: str
    base_log: str
    error_file_log: str
    info_file_log: str


class MongoDb(BaseModel):
    """Конфиг для сервиса mongodb"""
    host: str
    port: int
    db: str
    password: SecretStr
    username: str

    @property
    def url(self):
        return (f'mongodb://{self.username}:{self.password.get_secret_value()}'
                f'@{self.host}:{self.port}/?authSource=admin')


class SmtpConfig(BaseModel):
    """Конфиг для отправки сообщений по email"""
    server: str
    gmail: str
    app_psw: SecretStr
    port: int


class BaseConfig(BaseSettings):
    """Базовый конфиг для хранения настроек проекта"""
    postgres: PostgresqlSettings
    redis: RedisSettings
    jwt_access: JWTSettings
    jwt_refresh: JWTSettings
    upload_file_path: str = f'{BASE_DIR}/user-files'
    log_info: LogLevelInfo
    mongodb: MongoDb
    smtp: SmtpConfig
    app_key: bytes
    mode: AppMode = AppMode.DEV

    @field_validator('upload_file_path')
    @classmethod
    def create_dir(cls, v):
        path = Path(v)
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
        return v


class DevelopConfig(BaseConfig):
    """Конфиг для разработки"""
    mode: AppMode = AppMode.DEV
    model_config = SettingsConfigDict(
        env_file=f'{BASE_DIR}/.dev.env',
        env_nested_delimiter='__',
        extra='ignore'
    )


class ProductionConfig(BaseConfig):
    """Конфиг для production"""
    mode: AppMode = AppMode.PROD
    model_config = SettingsConfigDict(
        env_file=f'{BASE_DIR}/.prod.env',
        env_nested_delimiter='__',
        extra='ignore'
    )


class TestingConfig(BaseConfig):
    """Конфиг для тестирования"""
    mode: AppMode = AppMode.TEST
    model_config = SettingsConfigDict(
        env_file=f'{BASE_DIR}/.test.env',
        env_nested_delimiter='__',
        extra='ignore'
    )


_config: None | BaseConfig = None

def create_config(mode: AppMode) -> BaseConfig:
    """
    Получение конфигурации приложения по типу режима работы:
    1) 'dev'
    2) 'test'
    3) 'production'
    :param mode: объект enum перечисления AppMode
    :return: объект BaseConfig с конфигураций приложения
    """
    global _config
    match mode:
        case AppMode.DEV:
            _config = DevelopConfig()
        case AppMode.PROD:
            _config = ProductionConfig()
        case AppMode.TEST:
            _config = TestingConfig()
        case _:
            raise ValueError(f"Неизвестный режим работы: {mode}, доступны (dev, test, prod)")
    return get_config()


def get_config() -> BaseConfig:
    if not _config:
        raise TypeError('Конфиг не был проинициализирован')
    return _config