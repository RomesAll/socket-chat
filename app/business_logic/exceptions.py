from uuid import UUID


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


class SaveIdRefreshTokenWhiteListError(Exception):
    """Ошибка сохранения id refresh токена"""
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.msg = f'Ошибка сохранения id refresh токена для пользователя {user_id}'
        super().__init__(self.msg)


class SessionKeyNotFound(Exception):
    """Не удалось найти сессионный ключ"""
    def __init__(self, user_id: str, session_id: UUID):
        self.user_id = user_id
        self.session_id = session_id
        self.msg = f'Не удалось найти id сессионного ключа {session_id} для пользователя {user_id}'
        super().__init__(self.msg)


class SaveSessionKeyError(Exception):
    """Ошибка сохранения сессионного ключа"""
    def __init__(self, user_id: str, session_id: UUID):
        self.user_id = user_id
        self.session_id = session_id
        self.msg = f'Не удалось сохранить сессионный ключ {session_id} для пользователя {user_id}'
        super().__init__(self.msg)