from typing import Final
from dataclasses import dataclass, fields


@dataclass(frozen=True, slots=True)
class BaseSaveDTO:
    """Базовый класс для всех DTO создания/сохранения."""


@dataclass(frozen=True, slots=True)
class BaseUpdateDTO:
    """Базовый класс для всех DTO обновления."""

    def get_not_null_attrs(self) -> dict:
        """Получить все заполненные поля"""
        result = {}
        for f in fields(self):
            value = getattr(self, f.name)
            if value is UNSET:
                continue
            result[f.name] = value
        return result


class _UnsetType:
    _instance: "_UnsetType | None" = None

    def __new__(cls) -> "_UnsetType":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __repr__(self) -> str:
        return "UNSET"

    def __bool__(self) -> bool:
        return False


UNSET: Final = _UnsetType()