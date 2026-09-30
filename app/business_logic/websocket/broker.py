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

    async def _listen(self):
        """Бесконечный цикл чтения канала, работает в отдельной задаче"""
        if self._pubsub is None:
            return
        try:
            async for message in self._pubsub.listen():
                if self._stopping:
                    break
                if message.get('type_package') != 'message':
                    continue
                try:
                    package = json.loads(message['data'])
                except Exception:
                    continue
                try:
                    await self._dispatch_package(package)
                except Exception:
                    continue
        except asyncio.CancelledError:
            raise
        except Exception:
            pass

    async def _dispatch_package(self, package: dict):
        """Обработка пакета"""
        target = package.get('target') or {}
        payload = package.get('payload') or {}
        type_message = target.get('type_message')

        match type_message:
            case 'chat':
                await self.manager.send_to_chat(UUID(target['chat_id']), payload)
            case 'user':
                await self.manager.send_to_user(target['user_id'], payload)
            case 'session':
                await self.manager.send_to_session(
                    target['user_id'],
                    UUID(target['session_id']),
                    payload,
                )
            case 'broadcast':
                await self.manager.broadcast(payload)
            case 'join_chat':
                sessions = self.manager.active_session.get(target['user_id'], {})
                for ws in sessions.values():
                    self.manager.join_in_chat(ws, UUID(target['chat_id']))
            case 'leave_chat':
                sessions = self.manager.active_session.get(target['user_id'], {})
                for ws in sessions.values():
                    self.manager.leave_chat(ws, UUID(target['chat_id']))

    async def _publish(self, package: dict):
        await self.redis.publish(self.CHANNEL, json.dumps(package))

    async def publish_to_chat(self, action_type: str, chat_id: UUID, data: dict):
        await self._publish({
            'target': {'type_message': 'chat', 'chat_id': str(chat_id)},
            'payload': {
                'action_type': action_type,
                'data': data
            },
        })

    async def publish_to_user(self, action_type: str, user_id: str, data: dict):
        await self._publish({
            'target': {'type_message': 'user', 'user_id': user_id},
            'payload': {
                'action_type': action_type,
                'data': data
            },
        })

    async def publish_to_session(self, action_type: str, user_id: str, session_id: UUID, data: dict):
        await self._publish({
            'target': {
                'type_message': 'session',
                'user_id': user_id,
                'session_id': str(session_id),
            },
            'payload': {
                'action_type': action_type,
                'data': data
            },
        })

    async def publish_broadcast(self, action_type: str, data: dict):
        await self._publish({
            'target': {'type_message': 'broadcast'},
            'payload': {
                'action_type': action_type,
                'data': data
            },
        })

    async def publish_join_chat(self, action_type: str, chat_id: UUID, user_id: str):
        await self._publish({
            'target': {'type_message': 'join_chat', 'chat_id': str(chat_id), 'user_id': user_id},
            'payload': {
                'action_type': action_type,
                'data': ''
            },
        })

    async def publish_leave_chat(self, action_type: str, chat_id: UUID, user_id: str):
        await self._publish({
            'target': {'type_message': 'leave_chat', 'chat_id': str(chat_id), 'user_id': user_id},
            'payload': {
                'action_type': action_type,
                'data': ''
            },
        })