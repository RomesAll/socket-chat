
class RedisConnectionError(Exception):
    """Сервер Redis выключен, упал, или указан неверный хост/порт"""
    def __init__(self, url: str, cause: str):
        self.url = url
        self.cause = cause
        self.msg = f'Не удалось подключится к redis url={self.url}, причина: {self.cause}'
        super().__init__(self.msg)


class AuthRedisError(Exception):
    """Неверный пароль или логин в URL"""
    def __init__(self, url: str, cause: str):
        self.url = url
        self.cause = cause
        self.msg = f'Неверные данные для подключения url={self.url}, причина: {self.cause}'
        super().__init__(self.msg)


class ResponseRedisError(Exception):
    """Ошибки redis"""
    def __init__(self, cause: str):
        self.cause = cause
        self.msg = f'Неверные данные для взаимодействия с redis, причина: {self.cause}'
        super().__init__(self.msg)


class DataErrorRedis(Exception):
    """Ошибка валидации данных на стороне Python"""
    def __init__(self, cause: str):
        self.cause = cause
        self.msg = f'Ошибка валидации данных на стороне Python, причина: {self.cause}'
        super().__init__(self.msg)