from typing import Callable
from app.infrastructure.database.repositories import MessageRepository, UserRepository
from sqlalchemy.ext.asyncio import AsyncSession as SqlAsyncSession
from app.infrastructure.database.repositories import ChatRepository, ChatReadRepository
from app.infrastructure.database.repositories import ChatMemberReadRepository, ChatMemberRepository
from app.infrastructure.database.repositories.message_attachment_repo import MessageAttachmentRepository
from app.infrastructure.database.repositories import RoomRepository, RoomReadRepository
from app.infrastructure.events.event_registry import EventRegistry, DataclassInstance
from app.shared.log_config import LogMixin


class UnitOfWork(LogMixin):
    """Паттерн unit of work (асинхронный)."""

    def __init__(self, sql_session: SqlAsyncSession, event_registry: EventRegistry):
        self.sql_session = sql_session

        self.msg_repo = MessageRepository(self.sql_session)
        self.msg_attach_repo = MessageAttachmentRepository(self.sql_session)

        self.chat_read_repo = ChatReadRepository(self.sql_session)
        self.chat_repo = ChatRepository(self.sql_session)

        self.chat_member_read_repo = ChatMemberReadRepository(self.sql_session)
        self.chat_member_repo = ChatMemberRepository(self.sql_session)

        self.room_read_repo = RoomReadRepository(self.sql_session)
        self.room_repo = RoomRepository(self.sql_session)

        self.user_repo = UserRepository(self.sql_session)

        self._event_registry = event_registry
        self._events: list[DataclassInstance] = []
        self._after_commit: list[Callable] = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        try:
            if exc_type:
                await self.sql_session.rollback()
            else:
                await self.sql_session.commit()

                for fn in self._after_commit:
                    try:
                        await fn()
                    except Exception:
                        self.log_error(f"after_commit failed: {fn}")

                for event in self._events:
                    try:
                        await self._event_registry.pub(event)
                    except Exception:
                        self.log_error(
                            f"Не удалось опубликовать событие "
                            f"{type(event).__name__}: {exc_val}"
                        )
        finally:
            await self.sql_session.close()
            self._events.clear()

    def add_event(self, event: DataclassInstance) -> None:
        """Зарегистрировать доменное событие для публикации после коммита."""
        self._events.append(event)

    def add_after_commit(self, fn: Callable):
        """
        Добавить в коллекцию вызываемый объект,
        который будет вып. после commit
        """
        self._after_commit.append(fn)