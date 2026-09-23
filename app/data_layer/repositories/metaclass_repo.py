from abc import ABCMeta
from app.data_layer.repositories.exception_handler import SqlExceptionHandler


class RepoMeta(ABCMeta):
    """
    Метакласс для репозиториев.
    Назначение:\n
    - обернуть все функции класса в декоратор для обработки ошибок
    """
    def __new__(cls, name, bases, attrs):
        new_class = super().__new__(cls, name, bases, attrs)
        handler = SqlExceptionHandler()
        return handler(new_class)