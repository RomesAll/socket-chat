from datetime import datetime
from sqlalchemy import LargeBinary, DateTime
from sqlalchemy.orm import mapped_column, Mapped
from .base import Base, StrIdMixin
from app.shared.dto.enums import RoleEnum


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