from datetime import datetime, timezone
from mongotic import MongoBaseModel, mapped_field, Mapped
from app.data_layer.models.events import EventType


class History(MongoBaseModel):
    """Модель для хранения истории изменения объектов бд"""
    __databasename__ = "messenger_db"
    __tablename__ = "history"

    payload: Mapped[dict] = mapped_field(description="Полезная нагрузка (payload) события в виде JSON/dict")
    type: Mapped[EventType] = mapped_field(description="Тип события")
    created_at: Mapped[datetime] = mapped_field(description='Время действия над объектом')