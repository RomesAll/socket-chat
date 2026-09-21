from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import mapped_column, Mapped, relationship
from .base import Base, UuidIsMixin

if TYPE_CHECKING:
    from .users import User


class Room(UuidIsMixin, Base):
    """Orm модель для хранения информации о комнатах"""
    name: Mapped[str] = mapped_column(String(20))
    description: Mapped[str] = mapped_column(String(100))
    avatar_url: Mapped[str] = mapped_column(default=None, nullable=True)
    owner_id: Mapped[str] = mapped_column(ForeignKey('user.id', ondelete='CASCADE'))
    is_private: Mapped[bool] = mapped_column(default=True)
    user: Mapped['User'] = relationship(back_populates='rooms')
