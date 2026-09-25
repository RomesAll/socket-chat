from enum import Enum
from datetime import datetime
from uuid import uuid4
from mongotic import MongoBaseModel
from pydantic import Field


class EventType(str, Enum):
    """Перечисление типов событий"""
    SEND_EMAIL = 'send_email'
    SEND_MESSAGE = 'send_message'
    NEW_USER = 'new_user'
    UPDATE_USER = 'update_user'
    DELETE_USER = 'delete_user'


class Status(str, Enum):
    """Перечисление статусов событий"""
    NEW = 'new'
    PROCESSED = 'processed'
    FAILED = 'failed'


class OutboxEvent(MongoBaseModel):
    """Универсальный контейнер для хранения любых доменных событий в MongoDB"""
    __databasename__ = "messenger_db"
    __tablename__ = "outbox_events"

    id: str = Field(default_factory=lambda: str(uuid4()), alias="_id")
    event_name: str = Field(..., description="Название события, например: MessageSentEvent")
    payload: dict = Field(..., description="Полезная нагрузка (payload) события в виде JSON/dict")
    status: Status = Field(default=Status.NEW, description="Статус: NEW, PROCESSED, FAILED")
    type: EventType = Field(..., description="Тип события")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    processed_at: datetime | None = Field(default=None)
    error_message: str | None = Field(default=None, description="Текст ошибки, если отправка зафейлилась")
