from dataclasses import dataclass
from datetime import date, datetime
from uuid import UUID


@dataclass(frozen=True, slots=True)
class UserAnalyticsReport:
    """DTO для хранения кол-ва созданных и удаленных пользователей по дням"""
    user_created: list[dict[date, int]]
    user_deleted: list[dict[date, int]]


@dataclass(frozen=True)
class ChatMemberAdded:
    """Документ аналитики добавления участника в чат."""
    chat_id: str
    user_id: str
    role: str
    occurred_at: datetime
    created_at: datetime


@dataclass(frozen=True)
class ChatMemberRemoved:
    """Документ аналитики удаления участника из чата."""
    chat_id: str
    user_id: str
    occurred_at: datetime
    created_at: datetime


@dataclass(frozen=True)
class ChatChangeOwner:
    """Документ аналитики передачи владения."""
    chat_id: str
    from_user_id: str
    to_user_id: str
    occurred_at: datetime
    created_at: datetime


@dataclass(frozen=True, slots=True)
class ChatAnalyticsReport:
    """DTO для хранения информации о добавленных и удаленных участников и владельцев чата по дням"""
    member_added: list[ChatMemberAdded]
    member_removed: list[ChatMemberRemoved]
    owner_changed: list[ChatChangeOwner]


@dataclass(frozen=True, slots=True)
class MessageAnalyticsReport:
    """DTO для хранения информации топ чатов и отправителей"""
    top_senders: list[dict]
    top_chats: list[dict]


@dataclass(frozen=True, slots=True)
class RoomAnalyticsReport:
    """DTO для хранения информации о созданных и удаленных комнат"""
    room_created: list[dict[date, int]]
    room_deleted: list[dict[date, int]]


@dataclass(frozen=True, slots=True)
class MessageSent:
    """DTO для хранения информации о добавленном сообщении"""
    message_id: str
    chat_id: str
    sender_id: str | None
    message_type: str
    text_length: int
    occurred_at: datetime
    created_at: datetime


@dataclass(frozen=True, slots=True)
class TopSender:
    """DTO для хранения топ отправителей по сообщениям"""
    user_id: str
    count: int


@dataclass(frozen=True, slots=True)
class TopChat:
    """DTO для хранения топ чатов по сообщениям"""
    chat_id: UUID
    count: int


@dataclass(frozen=True, slots=True)
class CountMessagesByDay:
    """DTO для хранения кол-ва сообщений по дням"""
    day: date
    count: int


@dataclass(frozen=True, slots=True)
class CountCreatedRoom:
    """DTO для хранения кол-ва созданных комнат"""
    day: date
    count: int


@dataclass(frozen=True, slots=True)
class CountDeletedRoom:
    """DTO для хранения кол-ва удаленных комнат"""
    day: date
    count: int


@dataclass(frozen=True, slots=True)
class CountCreatedUser:
    """DTO для хранения кол-ва созданных пользователей"""
    day: date
    count: int


@dataclass(frozen=True, slots=True)
class CountDeletedUser:
    """DTO для хранения кол-ва удаленных пользователей"""
    day: date
    count: int
