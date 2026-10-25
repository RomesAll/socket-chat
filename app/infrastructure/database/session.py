from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


class PostgresClient:
    """Клиент PostgreSQL, хранит подключение и фабрику создания сессий."""

    def __init__(self, url: str, echo: bool = False):
        self._engine = create_async_engine(url)
        self._session_factory = async_sessionmaker(
            bind=self._engine,
            expire_on_commit=False
        )

    @property
    def engine(self) -> AsyncEngine:
        return self._engine

    def session(self) -> AsyncSession:
        """Создать новую сессию. Закрывается в UnitOfWork паттерне"""
        return self._session_factory()

    async def ping(self) -> bool:
        """Проверить активность подключения к БД."""
        try:
            async with self._engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            return True
        except Exception:
            return False

    async def close(self) -> None:
        """Закрыть engine и пул соединений."""
        await self._engine.dispose()