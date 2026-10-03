from enum import Enum
from datetime import datetime, timezone
from mongotic import MongoBaseModel, mapped_field, Mapped


class EventType(str, Enum):
    """Перечисление типов событий"""
    SEND_EMAIL = 'SEND_EMAIL'
    SEND_VERIFY_CODE = 'SEND_VERIFY_CODE'

    CREATE_NEW_USER = 'CREATE_NEW_USER'
    UPDATE_USER = 'UPDATE_USER'
    DELETE_USER = 'DELETE_USER'
    SEND_ACTIVE_MONITOR_IN_USER = 'SEND_ACTIVE_MONITOR_IN_USER'
    SEND_DATE_USER_CONNECTION = 'SEND_DATE_USER_CONNECTION'

    SEND_MESSAGE_IN_CHAT = 'SEND_MESSAGE_IN_CHAT'
    UPDATE_MESSAGE_IN_CHAT = 'UPDATE_MESSAGE_IN_CHAT'
    DELETE_MESSAGE_IN_CHAT = 'DELETE_MESSAGE_IN_CHAT'

    CREATE_NEW_CHAT = 'CREATE_NEW_CHAT'
    UPDATE_CHAT = 'UPDATE_CHAT'
    DELETE_CHAT = 'DELETE_CHAT'
    ADD_MEMBER_IN_CHAT = 'ADD_MEMBER_IN_CHAT'
    REMOVE_MEMBER_IN_CHAT = 'REMOVE_MEMBER_IN_CHAT'
    SEND_ACTIVE_MONITOR_IN_CHAT = 'SEND_ACTIVE_MONITOR_IN_CHAT'

    CRETE_NEW_ROOM = 'NEW_ROOM'
    DELETE_ROOM = 'DELETE_ROOM'
    ADD_MEMBER_IN_ROOM = 'ADD_MEMBER_IN_ROOM'
    REMOVE_MEMBER_IN_ROOM = 'REMOVE_MEMBER_IN_ROOM'


class Status(str, Enum):
    """Перечисление статусов событий"""
    NEW = 'NEW'
    PROCESSED = 'PROCESSED'
    FAILED = 'FAILED'
    PROCESSING = 'PROCESSING'


class OutboxEvent(MongoBaseModel):
    """Универсальный контейнер для хранения любых доменных событий в MongoDB"""
    __databasename__ = "messenger_db"
    __tablename__ = "outbox_events"

    event_name: Mapped[str] = mapped_field(description="Название события, например: MessageSentEvent")
    payload: Mapped[dict] = mapped_field(description="Полезная нагрузка (payload) события в виде JSON/dict")
    status: Mapped[Status] = mapped_field(default=Status.NEW, description="Статус: NEW, PROCESSED, FAILED")
    type: Mapped[EventType] = mapped_field(description="Тип события")
    created_at: Mapped[datetime] = mapped_field(default_factory=lambda: datetime.now(tz=timezone.utc))
    processed_at: Mapped[datetime | None] = mapped_field(default=None)
    error_message: Mapped[str | None] = mapped_field(default=None, description="Текст ошибки, если отправка не удалось обработать")