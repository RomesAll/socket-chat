from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey
from sqlalchemy.orm import mapped_column, Mapped, relationship
from enum import Enum
from uuid import UUID
from .base import Base, UuidIsMixin

if TYPE_CHECKING:
    from .rooms import Room


class ChatType(str, Enum):
    """Перечисление типов чатов"""
    PRIVATE = 'private'
    GROUP = 'group'


class Chat(UuidIsMixin, Base):
    """Orm модель для хранения информации о чатах"""
    type: Mapped[ChatType]
    room_id: Mapped[UUID] = mapped_column(
        ForeignKey('room.id', ondelete='CASCADE'),
        nullable=True,
        default=None
    )
    room: Mapped['Room'] = relationship(back_populates='chat')
    members: Mapped[list['ChatMember']] = relationship(back_populates='chat', cascade='all, delete-orphan',)


class ChatMember(Base):
    """Orm модель для хранения информации об участниках чата"""
    chat_id: Mapped[UUID] = mapped_column(
        ForeignKey('room.id', ondelete='CASCADE'),
        nullable=True,
        default=None
    )
    user_id: Mapped[str] = mapped_column(
        ForeignKey('room.id', ondelete='CASCADE'),
        nullable=True,
        default=None
    )
    last_read_message_id: Mapped[UUID] = mapped_column(
        default=None,
        nullable=True
    )
    mute: Mapped[bool] = mapped_column(default=False)
    chat: Mapped['ChatMember'] = relationship(back_populates='members')