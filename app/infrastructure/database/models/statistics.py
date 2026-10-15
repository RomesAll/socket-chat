from datetime import date, datetime
from uuid import UUID
from mongotic import MongoBaseModel, mapped_field, Mapped


class ChatStatistic(MongoBaseModel):
    """Модель для хранения статистики чата"""
    __databasename__ = "messenger_db"
    __tablename__ = "chat_statistics"

    chat_id: Mapped[UUID]
    total_message: Mapped[int] = mapped_field(default=0, description='Кол-во сообщений в чате')
    count_users: Mapped[int] = mapped_field(default=0, description='Кол-во пользоват. в чате')
    last_message_at: Mapped[datetime | None] = mapped_field(default=None, description='Время последнего сообщения')
    messages_by_type: Mapped[dict[str, int]] = mapped_field(default_factory=dict, description='Типы сообщений')
    hourly_activity_monitored: Mapped[dict[str, int]] = mapped_field(default_factory=dict, description='Пик активности по пользователям')


class UserStatistic(MongoBaseModel):
    """Модель для хранения статистики пользователя"""
    __databasename__ = "messenger_db"
    __tablename__ = "user_statistics"

    user_id: Mapped[str]
    total_message: Mapped[int] = mapped_field(default=0, description='Кол-во сообщений пользователя')
    max_hourly_activity_pick: Mapped[float] = mapped_field(default=0.0, description='Пик активности пользователя')
    messages_by_type: Mapped[dict[str, int]] = mapped_field(default_factory=dict, description='Кол-во типов сообщений')
    first_message_at: Mapped[datetime | None] = mapped_field(default=None, description='Время первого сообщения')
    last_message_at: Mapped[datetime | None] = mapped_field(default=None, description='Время последнего сообщения')
    last_connection: Mapped[datetime | None] = mapped_field(default=None, description='Время последнего подключения')
    total_chats_count: Mapped[int] = mapped_field(default=0, description='Кол-во чатов')


class GeneralMessengerStat(MongoBaseModel):
    """Модель для хранения общей статистики мессенджера"""
    __databasename__ = "messenger_db"
    __tablename__ = "general_statistics"

    created_at: Mapped[date]
    count_email_send: Mapped[int] = mapped_field(default=0, description='Кол-во отправленных сообщений по почте')
    count_code_send: Mapped[int] = mapped_field(default=0, description='Кол-во отправленных кодов подтверждения')
    count_reg_users: Mapped[int] = mapped_field(default=0, description='Кол-во зарегистрированных пользователей')
    count_msg_send: Mapped[int] = mapped_field(default=0, description='Кол-во отправленных сообщений')
    count_delete_users: Mapped[int] = mapped_field(default=0, description='Кол-во удаленных пользователей')
    count_create_chat: Mapped[int] = mapped_field(default=0, description='Кол-во созданных чатов')
    count_create_room: Mapped[int] = mapped_field(default=0, description='Кол-во созданных комнат')
    count_delete_room: Mapped[int] = mapped_field(default=0, description='Кол-во удаленных комнат')