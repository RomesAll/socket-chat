from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, declared_attr
from uuid import UUID
import re


class Base(DeclarativeBase):
    """Базовый класс для orm моделей sqlalchemy"""
    @classmethod
    @declared_attr.directive
    def __tablename__(cls) -> str:
        """
        Автоматическое определение названия таблицы по название класса.
        Превращает CamelCase в snake_case
        """
        return re.sub(r'(?<!^)(?=[A-Z])', r'_', cls.__name__).lower()


class IntIdMixin:
    """Миксин с id типом int для primary key модели"""
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)


class StrIdMixin:
    """Миксин с id типом str для primary key модели"""
    id: Mapped[str] = mapped_column(primary_key=True)


class UuidIsMixin:
    """Миксин с id типом uuid для primary key модели"""
    id: Mapped[UUID] = mapped_column(primary_key=True)