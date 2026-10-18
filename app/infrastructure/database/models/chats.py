from datetime import datetime
from sqlalchemy import ForeignKey
from sqlalchemy.orm import mapped_column, Mapped
from uuid import UUID
from .base import Base, UuidIsMixin
from app.shared.dto.enums import ChatRole, ChatType


class Chat(UuidIsMixin, Base):
    """Orm модель для хранения информации о чатах"""
    type: Mapped[ChatType]
    is_active: Mapped[bool] = mapped_column(default=True)
    last_message_at: Mapped[datetime | None] = mapped_column(
        default=None, nullable=True,
    )
    last_message_id: Mapped[UUID | None] = mapped_column(
        default=None, nullable=True,
    )


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
    role: Mapped[ChatRole] = mapped_column(default=ChatRole.MEMBER)
    last_read_message_id: Mapped[UUID | None] = mapped_column(
        default=None,
        nullable=True,
    )
    mute: Mapped[bool] = mapped_column(default=False, nullable=False)