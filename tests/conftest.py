from alembic.config import Config, command
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.shared.config import create_config, AppMode
import pytest


config = create_config(mode=AppMode.TEST)


@pytest.fixture(scope='session', autouse=True)
def migration_db():
    """
    Глобальная фикстура: срабатывает один раз при старте тестов.
    Накатывает миграции Alembic на тестовую БД перед тестами и откатывает после
    """
    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option('sqlalchemy.url', config.postgres.url)
    command.upgrade(alembic_cfg, 'head')
    yield
    command.downgrade(alembic_cfg, 'base')


@pytest.fixture(scope='session')
async def async_engine():
    """
    Фикстура для создания пула соединений (асинхронного движка)
    на уровне всей сессии
    """
    engine = create_async_engine(config.postgres.url, echo=False)
    yield engine
    await engine.dispose()


@pytest.fixture(scope='function')
async def sql_session(async_engine):
    """
    Главная фикстура для тестов. Вызывается перед каждым тестом.
    Она отдает сессию и делает ROLLBACK в конце,
    чтобы тесты не влияли на тестовую бд
    """
    session_factory = async_sessionmaker(bind=async_engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session
        await session.rollback()