from typing import Final
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class BaseSaveDTO:
    """Базовый класс для всех DTO создания/сохранения."""


@dataclass(frozen=True, slots=True)
class BaseUpdateDTO:
    """Базовый класс для всех DTO обновления."""


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