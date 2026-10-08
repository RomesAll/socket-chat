from datetime import datetime
from enum import Enum
from sqlalchemy import LargeBinary, ForeignKey, DateTime
from sqlalchemy.orm import mapped_column, Mapped
from .base import Base, StrIdMixin


class RoleEnum(str, Enum):
    """Перечисление списка ролей"""
    DEFAULT_USER = 'default_user'
    ADMIN = 'admin'
    SUPER_ADMIN = 'super_admin'


class User(StrIdMixin, Base):
    """Orm модель для хранения информации о пользователях"""
    display_name: Mapped[str]
    avatar_url: Mapped[str] = mapped_column(
        default=None,
        nullable=True
    )
    description: Mapped[str] = mapped_column(default=None, nullable=True)
    years_old: Mapped[int] = mapped_column(default=None, nullable=True)
    role: Mapped[RoleEnum] = mapped_column(default=RoleEnum.DEFAULT_USER)
    email: Mapped[str] = mapped_column(unique=True)
    password: Mapped[bytes] = mapped_column(LargeBinary(60))
    last_seen_at: Mapped[datetime] = mapped_column(default=None, nullable=True)
    is_deleted: Mapped[bool] = mapped_column(default=False)
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )