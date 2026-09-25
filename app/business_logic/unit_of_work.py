import asyncio
from app.data_layer.models.events import OutboxEvent, Status, EventType
from app.data_layer.repositories import MessageRepository, ChatRepository, RoomRepository, UserRepository
from mongotic.asyncio import AsyncSession as MongoSession
from sqlalchemy.ext.asyncio import AsyncSession as SqlAsyncSession


class UnitOfWork:
    """Паттерн unit of work (асинхронный)"""
    def __init__(self, sql_session: SqlAsyncSession, mongo_session: MongoSession | None = None):
        self.sql_session = sql_session
        self.mongo_session = mongo_session
        self.msg_repo = MessageRepository(self.sql_session)
        self.chat_repo = ChatRepository(self.sql_session)
        self.room_repo = RoomRepository(self.sql_session)
        self.user_repo = UserRepository(self.sql_session)
        self._events = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        try:
            if exc_type:
                await self.rollback()
            else:
                await self.commit()
        finally:
            await self.sql_session.close()
            if self.mongo_session:
                await self.mongo_session.close()

    def add_event(self, event_name: str, payload: dict, event_type: EventType):
        self._events.append({
            'event_name': event_name,
            'payload': payload,
            'event_type': event_type
        })

    async def commit(self):
        """Строгий атомарный коммит в обе базы данных"""
        if not self.mongo_session and self._events:
            raise RuntimeError("Попытка сохранить события, но mongo_session не инициализирована в UoW!")
        if self._events and self.mongo_session:
            for event in self._events:
                event_orm = OutboxEvent(
                    event_name=event["event_name"],
                    payload=event["payload"],
                    status=Status.NEW,
                    type=event['type']
                )
                self.mongo_session.add(event_orm)
        await self.sql_session.commit()
        if self.mongo_session:
            await self.mongo_session.commit()
        self._events.clear()

    async def rollback(self):
        """Откат обеих баз данных в случае ошибки бизнес-логики"""
        await self.sql_session.rollback()
        if self.mongo_session:
            await asyncio.to_thread(self.mongo_session.rollback)