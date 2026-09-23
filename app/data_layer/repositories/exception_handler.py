import functools
import inspect
from typing import Callable
from sqlalchemy.exc import IntegrityError, DatabaseError, DBAPIError, InterfaceError, TimeoutError
from app.data_layer.exceptions import IntegrityDBError, DBError, DBConnectionError, DBInterfaceError, \
    DBTimeoutError, RecordNotFound


class SqlExceptionHandler:
    """
    Класс декоратор для обработки ошибок sqlalchemy
    """
    def __call__(self, cls):
        for attr_name, attr_value in cls.__dict__.items():
            #Пропуск dunder методов
            if attr_name.startswith("__") and attr_name.endswith("__"):
                continue
            #Оборачиваем, если функция асинхронная
            if not inspect.iscoroutinefunction(attr_value):
                continue
            if getattr(attr_value, "__wrapped_by_sql_handler__", False):
                continue
            setattr(cls, attr_name, self._wrap_method(attr_value))
        return cls

    @staticmethod
    def _wrap_method(method: Callable):
        """Метод обертка для методов репозитория с обработкой ошибок"""
        @functools.wraps(method)
        async def wrapper(*args, **kwargs):
            try:
                result = await method(*args, **kwargs)
                return result
            except RecordNotFound:
                raise
            except IntegrityError as e:
                """Исключения связанные с нарушение целостности данных"""
                raise IntegrityDBError(e.orig)
            except InterfaceError as e:
                """Исключения связанные с неверным логином, паролем"""
                raise DBInterfaceError(e.orig)
            except DatabaseError as e:
                """Исключения связанные с ошибками бд"""
                raise DBError(e.orig)
            except DBAPIError as e:
                """Исключения связанные с api бд"""
                raise DBConnectionError(e)
            except TimeoutError as e:
                """Исключения связанные с таймаутом"""
                raise DBTimeoutError(e)
            except Exception as e:
                """Неизвестные исключения"""
                raise DBError(str(e))
        wrapper.__wrapped_by_sql_handler__ = True
        return wrapper