from datetime import datetime
from uuid import UUID
from mongotic import MongoBaseModel, mapped_field, Mapped


class ChatStatistic(MongoBaseModel):
    """Модель для хранения статистики чата"""
    __databasename__ = "messenger_db"
    __tablename__ = "chat_statistics"

    chat_id: Mapped[UUID]
    total_message: Mapped[int] = mapped_field(default=0)
    count_users: Mapped[int] = mapped_field(default=0)
    last_message_at: Mapped[datetime | None] = mapped_field(default=None)
    messages_by_type: Mapped[dict[str, int]] = mapped_field(default_factory=dict)
    hourly_activity_monitored: Mapped[dict[str, int]] = mapped_field(default_factory=dict)


class UserStatistic(MongoBaseModel):
    """Модель для хранения статистики пользователя"""
    __databasename__ = "messenger_db"
    __tablename__ = "user_statistics"

    user_id: Mapped[str]
    total_message: Mapped[int] = mapped_field(default=0)
    hourly_activity_pick: Mapped[int] = mapped_field(default=0)
    messages_by_type: Mapped[dict[str, int]] = mapped_field(default_factory=dict)
    first_message_at: Mapped[str | None] = mapped_field(default=None)
    last_message_at: Mapped[str | None] = mapped_field(default=None)
    last_connection: Mapped[str | None] = mapped_field(default=None)
    current_streak_days: Mapped[int] = mapped_field(default=0)
    max_streak_days: Mapped[int] = mapped_field(default=0)
    total_chats_count: Mapped[int] = mapped_field(default=0)