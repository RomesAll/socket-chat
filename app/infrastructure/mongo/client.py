from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase


class MongoClient:
    """Клиента MongoDB, хранить подключение к MongoDB серверу."""

    def __init__(
            self,
            url: str,
            db_name: str,
            pool_size: int = 100,
            timeout_ms: int = 5000
    ):
        self._client = AsyncIOMotorClient(
            url,
            maxPoolSize=pool_size,
            serverSelectionTimeoutMS=timeout_ms,
        )
        self._db: AsyncIOMotorDatabase = self._client[db_name]

    @property
    def db(self) -> AsyncIOMotorDatabase:
        return self._db

    async def ping(self) -> bool:
        """Проверить активность подключения к БД."""
        try:
            await self._client.admin.command("ping")
            return True
        except Exception:
            return False

    async def close(self) -> None:
        """Закрыть клиент и пул соединений."""
        self._client.close()
