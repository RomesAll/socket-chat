from functools import wraps
from redis.exceptions import *
from app.business_logic.exceptions import *
from app.shared.config import get_config


def _get_url() -> str:
    return get_config().redis.url


def exception_handler(generate_exc: bool = False):
    """Обработчик redis исключений"""
    def wrapper_func(func):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            exc = None
            try:
                result = await func(self, *args, **kwargs)
                return result
            except AuthenticationError as e:
                exc = AuthRedisError(_get_url(), str(e))
            except TimeoutError as e:
                exc = RedisConnectionError(_get_url(), str(e))
            except ConnectionError as e:
                exc = RedisConnectionError(_get_url(), str(e))
            except DataError as e:
                exc = DataErrorRedis(str(e))
            except ResponseError as e:
                exc = ResponseRedisError(str(e))
            except Exception as e:
                exc = Exception(e)
            if exc and generate_exc:
                raise exc
            return None
        return wrapper
    return wrapper_func