from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import mapped_column, Mapped, relationship
from enum import Enum
from uuid import UUID
from .base import Base, UuidIsMixin

if TYPE_CHECKING:
    from .users import User
    from .chats import Chat


class RoomRole(str, Enum):
    """Перечисление ролей в комнатах"""
    OWNER = 'owner'
    ADMIN = 'admin'
    MEMBER = 'member'


class Room(UuidIsMixin, Base):
    """Orm модель для хранения информации о комнатах"""
    name: Mapped[str] = mapped_column(String(20))
    description: Mapped[str] = mapped_column(String(100))
    avatar_url: Mapped[str] = mapped_column(default=None, nullable=True)
    owner_id: Mapped[str] = mapped_column(ForeignKey('user.id', ondelete='CASCADE'))
    is_private: Mapped[bool] = mapped_column(default=True)
    owner: Mapped['User'] = relationship(back_populates='owned_rooms')
    members: Mapped[list['RoomMember']] = relationship(
        back_populates='room',
        cascade='all, delete-orphan',
    )
    chat: Mapped['Chat'] = relationship(back_populates='room')


class RoomMember(Base):
    """Orm модель для хранения информации об участниках комнаты"""
    room_id: Mapped[UUID] = mapped_column(ForeignKey('room.id', ondelete='CASCADE'), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey('user.id', ondelete='CASCADE'), primary_key=True)
    role: Mapped[RoomRole] = mapped_column(default=RoomRole.MEMBER)
    room: Mapped['Room'] = relationship(back_populates='members')
    user: Mapped['User'] = relationship(back_populates='room_members')