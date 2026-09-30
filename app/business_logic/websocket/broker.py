import asyncio
import json
from uuid import UUID
import redis.asyncio as redis
from .manager import UserConnectionManager


class WSBroker:
    """
    Класс для реализации Redis Pub/Sub между воркерами
    - Публикует сообщения в канал
    - Слушает канал в фоновой задаче через asyncio
    - Отправляет сообщения в канал
    """
    CHANNEL = 'ws:broadcast'

    def __init__(self, redis_client: redis.Redis, manager: UserConnectionManager):
        self.redis = redis_client
        self.manager = manager
        self._pubsub: redis.client.PubSub | None = None
        self._task: asyncio.Task | None = None
        self._stopping = False

    async def start(self):
        """Подписаться на канал и запустить фоновое прослушивание"""
        self._stopping = False
        self._pubsub = self.redis.pubsub()
        await self._pubsub.subscribe(self.CHANNEL)
        self._task = asyncio.create_task(self._listen())

    async def stop(self):
        """Остановить прослушивание и закрыть pubsub"""
        self._stopping = True
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        if self._pubsub is not None:
            try:
                await self._pubsub.unsubscribe(self.CHANNEL)
            except Exception:
                pass
            await self._pubsub.close()
            self._pubsub = None