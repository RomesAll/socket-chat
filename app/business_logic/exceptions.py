from uuid import UUID


class VerifyCodeInCorrect(Exception):
    """Введенный код подтверждения неверный"""
    def __init__(self,):
        self.message = 'Введенный код подтверждения неверный'
        super().__init__(self.message)


class VerifyCodeStorageError(Exception):
    """Не удалось получить код подтверждения из кеша"""
    def __init__(self,):
        self.message = ('Не удалось найти код подтверждения, '
                        'т.к. сервис временно недоступен')
        super().__init__(self.message)


class SaveIdRefreshTokenWhiteListError(Exception):
    """Неудачная попытка сохранения id refresh токена"""
    def __init__(self, user_id: str):
        self.message = f'Не удалось сохранить id refresh токена пользователя {user_id} в white list'
        super().__init__(self.message)


class RefreshTokenInActive(Exception):
    """Refresh токен больше не активен"""
    def __init__(self, user_id: str, token_id):
        self.user_id = user_id
        self.message = f'Refresh токен больше не активен для пользователя {user_id}, токен id: {token_id}'
        super().__init__(self.message)


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


class SaveCodeError(Exception):
    """Ошибка сохранения кода подтверждения"""
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.msg = f'Не удалось сохранить код подтверждения для пользователя {user_id}'
        super().__init__(self.msg)


class UnsupportedFileTypeError(Exception):
    """Тип файла не поддерживается"""
    def __init__(self, msg):
        self.message = msg
        super().__init__(self.message)


class UrlTokenNotFound(Exception):
    """Ошибка поиска url токена"""
    def __init__(self, url):
        self.msg = f'Не удалось найти токен {url}'
        super().__init__(self.msg)


class UrlTokenIsRevoked(Exception):
    """Токен был отозван"""
    def __init__(self, url):
        self.msg = f'Переданный токен {url} существует, но он недействителен'
        super().__init__(self.msg)


class UrlTokenMaxUses(Exception):
    """Токеном воспользовалось максимальное кол-во пользователей"""
    def __init__(self, url):
        self.msg = f'Переданный токен {url} существует, но закончилось кол-во использований'
        super().__init__(self.msg)


class ChangeOwnerRoomPermDenied(Exception):
    """Нет доступа для смены владельца комнаты"""
    def __init__(self, user_id, room_id):
        self.msg = f'Пользователь {user_id} не может сменить владельца в комнате {room_id}, т.к. у него нет прав на это'
        super().__init__(self.msg)


class OwnerInRoomEmpty(Exception):
    """Не удалось найти владельца комнаты"""
    def __init__(self, room_id):
        self.msg = f'У комнаты {room_id} не удалось найти владельца'
        super().__init__(self.msg)


class AuthError(Exception):
    """Ошибка аутентификации пользователя"""
    def __init__(self):
        self.msg = f'Передан неверный логин или пароль'
        super().__init__(self.msg)