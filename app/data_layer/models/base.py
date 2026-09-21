from datetime import datetime
from typing import Any
from sqlalchemy import DateTime, func
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

    def __repr__(self) -> str:
        """
        Отображение объектов orm класса со скрытием приватных атрибутов
        Атрибуты, которые сейчас скрываются:
        1) password
        2) email (заменяются '*')
        :return:
        """
        cols = []
        for col in self.__table__.columns.keys():
            value = getattr(self, col)
            if (handle_value := self.check_private_columns(col, value)) is None:
                continue
            cols.append((col, handle_value))
        sorted_cols = sorted(cols, key=self.sorted_column)
        result = [f'{col}={value}' for col, value in sorted_cols]
        return f"<{self.__class__.__name__}({', '.join(result)})>"

    @staticmethod
    def sorted_column(items) -> tuple:
        """Функция сортировки для того, чтобы атрибут id был всегда на первом месте"""
        col_name = items[0]
        return (col_name != 'id', col_name)

    @staticmethod
    def check_private_columns(column: str, value: Any) -> None | str:
        """Проверка атрибутов на приватность"""
        if re.fullmatch(r'(pass|passw\w*)', column):
            return None
        if re.fullmatch(r'(email|mail|gmail|\w*mail)', column):
            return re.sub(r'(\w)(\w+)(@\w+\.\w+)', Base.mask_email, value)
        return value

    @staticmethod
    def mask_email(match):
        """Маска для почты, чтобы заменить первые символы *"""
        first_letter = match.group(1)
        hidden_part = "*" * len(match.group(2))
        domain = match.group(3)
        return f"{first_letter}{hidden_part}{domain}"


class IntIdMixin:
    """Миксин с id типом int для primary key модели"""
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)


class StrIdMixin:
    """Миксин с id типом str для primary key модели"""
    id: Mapped[str] = mapped_column(primary_key=True)


class UuidIsMixin:
    """Миксин с id типом uuid для primary key модели"""
    id: Mapped[UUID] = mapped_column(primary_key=True)