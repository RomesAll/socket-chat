from datetime import timedelta

import pytest
from typing import AsyncGenerator

from motor.motor_asyncio import AsyncIOMotorClient
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.infrastructure.database.models import Base
from app.infrastructure.security import JWTFacade, JWTAccessManager, JWTRefreshManager
from app.shared.config import create_config, AppMode
from mongotic.asyncio import AsyncSession as MongoticAsyncSession
from mongotic.asyncio import create_async_engine as mongo_create_async_engine

# Инициализация тестового конфига из файла .test.env
config = create_config(mode=AppMode.TEST)
TEST_DATABASE_URL = config.postgres.url
TEST_DATABASE_MONGO_URL = config.mongodb.url

# Создание асинхронного движка и фабрики сессии sqlalchemy
test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
test_mongo_engine = mongo_create_async_engine(host=TEST_DATABASE_MONGO_URL, uuidRepresentation="standard")
TestingSessionLocal = async_sessionmaker(bind=test_engine, expire_on_commit=False)


@pytest.fixture(scope='function', autouse=True)
async def setup_data_base():
    """Создать таблицы перед началом выполнения тестов и удалить после."""
    async with test_engine.begin() as engine:
        await engine.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope='function')
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Получить изолированную сессию для каждого теста с
    механизмом SAVEPOINT (вложенных транзакций).

    Любые commit() внутри теста не запишут данные в базу данных насовсем,
    так как фикстура сделает полный rollback после завершения теста.
    """
    async with test_engine.connect() as conn:
        # создание транзакции
        transaction = await conn.begin()
        # создание сессии
        session = TestingSessionLocal(bind=conn)
        # установка SAVEPOINT внутри транзакции
        await session.begin_nested()
        yield session
        # откат всех изменений
        await session.close()
        await transaction.rollback()


@pytest.fixture(scope='function')
async def db_mongo_session() -> AsyncGenerator[AsyncSession, None]:
  """Фикстура для получения асинхронной сессии mongotic."""
  async with MongoticAsyncSession(bind=test_mongo_engine) as session:
    yield session
    session.rollback()


@pytest.fixture(scope='function')
async def redis_client():
    client = Redis.from_url(config.redis.url)
    return client


@pytest.fixture(scope='function')
async def mongo_client():
    client = AsyncIOMotorClient(config.mongodb.url)
    db = client['test_db']
    collection = db['test_collection']
    return collection


@pytest.fixture(scope='function')
async def jwt_facade() -> JWTFacade:
    facade = JWTFacade(
        access_manager=JWTAccessManager(
            secret_key=config.jwt_access.secretkey,
            alg=config.jwt_access.algorithm,
            expires_delta=timedelta(config.jwt_access.expiresdelta)
        ),
        refresh_manager=JWTRefreshManager(
            secret_key=config.jwt_refresh.secretkey,
            alg=config.jwt_refresh.algorithm,
            expires_delta=timedelta(config.jwt_refresh.expiresdelta)
        )
    )
    return facade