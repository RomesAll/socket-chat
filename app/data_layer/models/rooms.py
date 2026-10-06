from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import mapped_column, Mapped
from enum import Enum
from uuid import UUID
from .base import Base, UuidIsMixin


class RoomRole(str, Enum):
    """Перечисление ролей в комнатах"""
    OWNER = 'owner'
    ADMIN = 'admin'
    MEMBER = 'member'


class Room(UuidIsMixin, Base):
    """Orm модель для хранения информации о комнатах"""
    name: Mapped[str] = mapped_column(String(20))
    description: Mapped[str] = mapped_column(String(100), default=None, nullable=True)
    avatar_url: Mapped[str] = mapped_column(default=None, nullable=True)
    owner_id: Mapped[str | None] = mapped_column(
        ForeignKey('user.id', ondelete='SET NULL'),
        nullable=True
    )


class RoomMember(Base):
    """Orm модель для хранения информации об участниках комнаты"""
    room_id: Mapped[UUID] = mapped_column(ForeignKey('room.id', ondelete='CASCADE'), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey('user.id', ondelete='CASCADE'), primary_key=True)
    role: Mapped[RoomRole] = mapped_column(default=RoomRole.MEMBER)