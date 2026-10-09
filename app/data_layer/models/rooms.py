from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import mapped_column, Mapped
from uuid import UUID
from .base import Base
from app.shared.dto.enums import RoomRole


class Room(Base):
    """Orm модель для хранения информации о комнатах"""
    chat_id: Mapped[UUID] = mapped_column(
        ForeignKey('chat.id', ondelete='CASCADE'),
        primary_key=True
    )
    name: Mapped[str] = mapped_column(String(20))
    description: Mapped[str | None] = mapped_column(String(100), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(default=None, nullable=True)
    max_users: Mapped[int] = mapped_column(default=30)
    owner_id: Mapped[str | None] = mapped_column(
        ForeignKey('user.id', ondelete='SET NULL'),
        nullable=True
    )


class RoomMember(Base):
    """Orm модель для хранения информации об участниках комнаты"""
    room_id: Mapped[UUID] = mapped_column(ForeignKey('room.chat_id', ondelete='CASCADE'), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey('user.id', ondelete='CASCADE'), primary_key=True)
    role: Mapped[RoomRole] = mapped_column(default=RoomRole.MEMBER)
    is_access_private_chat: Mapped[bool] = mapped_column(default=False)