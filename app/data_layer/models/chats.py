from sqlalchemy import ForeignKey
from sqlalchemy.orm import mapped_column, Mapped
from enum import Enum
from uuid import UUID
from .base import Base, UuidIsMixin


class ChatType(str, Enum):
    """Перечисление типов чатов"""
    PRIVATE = 'private'
    GROUP = 'group'


class Chat(UuidIsMixin, Base):
    """Orm модель для хранения информации о чатах"""
    name: Mapped[str]
    room_id: Mapped[UUID | None] = mapped_column(
        ForeignKey('room.id', ondelete='CASCADE'),
        nullable=True,
        default=None
    )
    is_private: Mapped[bool] = mapped_column(default=False)


class ChatMember(Base):
    """Orm модель для хранения информации об участниках чата"""
    chat_id: Mapped[UUID] = mapped_column(
        ForeignKey('chat.id', ondelete='CASCADE'),
        primary_key=True
    )
    user_id: Mapped[str] = mapped_column(
        ForeignKey('user.id', ondelete='CASCADE'),
        primary_key=True
    )
    last_read_message_id: Mapped[UUID] = mapped_column(
        default=None,
        nullable=True
    )
    mute: Mapped[bool] = mapped_column(default=False)