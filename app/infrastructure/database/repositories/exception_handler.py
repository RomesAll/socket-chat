import functools
import inspect
from logging import getLogger
from typing import Callable
from sqlalchemy.exc import IntegrityError, DatabaseError, DBAPIError, InterfaceError, TimeoutError
from app.infrastructure.database.exceptions import IntegrityDBError, DBError, DBConnectionError, DBInterfaceError, \
    DBTimeoutError
from app.shared.config import get_config


app_logger = getLogger(get_config().log_info.log_name)


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
            exc = None
            try:
                result = await method(*args, **kwargs)
                return result
            except IntegrityError as e:
                """Исключения связанные с нарушение целостности данных"""
                exc = IntegrityDBError(e.orig)
            except InterfaceError as e:
                """Исключения связанные с неверным логином, паролем"""
                exc = DBInterfaceError(e.orig)
            except DatabaseError as e:
                """Исключения связанные с ошибками бд"""
                exc = DBError(e.orig)
            except DBAPIError as e:
                """Исключения связанные с api бд"""
                exc = DBConnectionError(str(e))
            except TimeoutError as e:
                """Исключения связанные с таймаутом"""
                exc = DBTimeoutError()
            except Exception as e:
                """Неизвестные исключения"""
                exc = DBError(str(e))
            if exc:
                app_logger.error(
                    f"DB error in {method.__name__}: {type(exc).__name__}: {exc}"
                )
                raise exc
            return None
        wrapper.__wrapped_by_sql_handler__ = True
        return wrapper