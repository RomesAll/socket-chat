from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import mapped_column, Mapped
from uuid import UUID
from .base import Base


class Room(Base):
    """Orm модель для хранения информации о комнатах"""
    chat_id: Mapped[UUID] = mapped_column(
        ForeignKey('chat.id', ondelete='CASCADE'),
        primary_key=True
    )
    title: Mapped[str] = mapped_column(String(20))
    description: Mapped[str | None] = mapped_column(String(100), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(default=None, nullable=True)
    max_users: Mapped[int] = mapped_column(default=30)