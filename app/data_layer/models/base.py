from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from uuid import UUID


class Base(DeclarativeBase):
    """Базовый класс для orm моделей sqlalchemy"""
    pass


class IntIdMixin:
    """Миксин с id типом int для primary key модели"""
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)


class StrIdMixin:
    """Миксин с id типом str для primary key модели"""
    id: Mapped[str] = mapped_column(primary_key=True)


class UuidIsMixin:
    """Миксин с id типом uuid для primary key модели"""
    id: Mapped[UUID] = mapped_column(primary_key=True)