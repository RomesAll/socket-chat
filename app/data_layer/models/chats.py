from sqlalchemy import ForeignKey, String, CheckConstraint
from sqlalchemy.orm import mapped_column, Mapped
from uuid import UUID
from .base import Base, UuidIsMixin


class Chat(UuidIsMixin, Base):
    """Orm модель для хранения информации о чатах"""
    type: Mapped[str] = mapped_column(String(20))
    is_active: Mapped[bool] = mapped_column(default=True)

    __table_args__ = (
        CheckConstraint("type IN ('private', 'room')", name='check_type'),
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
    last_read_message_id: Mapped[UUID] = mapped_column(
        default=None,
        nullable=True
    )
    mute: Mapped[bool] = mapped_column(default=False)