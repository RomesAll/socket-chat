import secrets
from typing import Protocol


class CodeGenerator(Protocol):
    """Генератор числовых кодов."""

    def generate(self) -> int: ...


class SecretsCodeGenerator:
    """Класс для генерации криптостойкого код в диапазоне."""

    def __init__(self, min_value: int = 10000, max_value: int = 99999):
        if min_value > max_value:
            raise ValueError("Минимальное значение должно быть <= максимального")
        self._min = min_value
        self._max = max_value

    def generate(self) -> int:
        """Генерация кода."""
        return secrets.randbelow(self._max - self._min + 1) + self._min