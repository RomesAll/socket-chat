from datetime import datetime
from enum import Enum
from sqlalchemy import LargeBinary, ForeignKey
from sqlalchemy.orm import mapped_column, Mapped, relationship
from .base import Base, StrIdMixin, IntIdMixin


class RoleEnum(str, Enum):
    """Перечисление списка ролей"""
    DEFAULT_USER = 'default_user'
    ADMIN = 'admin'
    SUPER_ADMIN = 'super_admin'


class User(StrIdMixin, Base):
    """Orm модель для хранения информации о пользователях"""
    display_name: Mapped[str]
    avatar_url: Mapped[str]
    user_info_id: Mapped[int] = mapped_column(ForeignKey('user_info.id', ondelete='CASCADE'))
    user_info: Mapped['UserInfo'] = relationship(back_populates='user', uselist=False)


class UserInfo(IntIdMixin, Base):
    """Orm модель для хранения расширенной информации о пользователях"""
    description: Mapped[str] = mapped_column(default=None, nullable=True)
    years_old: Mapped[int] = mapped_column(default=None, nullable=True)
    role: Mapped[RoleEnum] = mapped_column(default=RoleEnum.DEFAULT_USER)
    email: Mapped[str] = mapped_column(unique=True)
    password_hash: Mapped[bytes] = mapped_column(LargeBinary(60))
    last_seen_at: Mapped[datetime] = mapped_column(default=None, nullable=True)
    user: Mapped['User'] = relationship(back_populates='user_info')