from datetime import datetime
from uuid import UUID
from mongotic import MongoBaseModel, mapped_field, Mapped
from app.infrastructure.database.models.events import EventType


class Audit(MongoBaseModel):
    """Модель для хранения истории (аудита) изменения объектов бд"""
    __databasename__ = "messenger_db"
    __tablename__ = "audit"

    actor_id: Mapped[str] = mapped_field(description='Пользователь выполнивший действие')
    target_id: Mapped[str | int | UUID] = mapped_field(description='id объекта над которым вып. действие')
    target_type: Mapped[str] = mapped_field(description='сущность над которой выполнено действие (User, Message и т.д.)')
    payload: Mapped[dict] = mapped_field(description="Полезная нагрузка (payload) события в виде JSON/dict")
    type_action: Mapped[EventType] = mapped_field(description="Тип события")
    created_at: Mapped[datetime] = mapped_field(description='Время действия над объектом')