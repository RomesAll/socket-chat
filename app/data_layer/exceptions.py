from pydantic import BaseModel


class DBConnectionError(Exception):
    """Ошибка подключения к бд"""
    def __init__(self, cause: str):
        self.url = cause
        self.msg = f'Ошибка подключения к БД {cause}'
        super().__init__(self.msg)


class DBTimeoutError(DBConnectionError):
    """Ошибка тайм-аута"""
    def __init__(self):
        self.msg = 'Тайм-аут ошибка'
        super().__init__(self.msg)


class DBError(Exception):
    """Неизвестная ошибка бд"""
    def __init__(self, cause='Неизвестная ошибка бд'):
        self.cause = cause
        self.msg = f'Ошибка бд, причина: {cause}'
        super().__init__(self.msg)


class RecordNotFound(DBError):
    """Запись не найдена"""
    def __init__(self, record_id, model, field):
        self.record_id = record_id
        self.model = model
        self.field = field
        self.msg = f'Не удалось найти запись {field}={record_id} в таблице {model}'
        super().__init__(self.msg)


class IntegrityDBError(DBError):
    """Ошибка нарушения целостности бд"""
    def __init__(self, cause='Неизвестная ошибка'):
        self.cause = cause
        self.msg = f'Нарушение целостности БД, {cause}'
        super().__init__(self.msg)


class DBInterfaceError(Exception):
    """Ошибка интерфейса"""
    def __init__(self, msg):
        self.msg = msg
        super().__init__(self.msg)


class OrmModelNotFound(Exception):
    """Не удалось найти orm модель по dto"""
    def __init__(self, dto: BaseModel):
        self.dto = dto
        self.msg = f'Не удалось найти orm модель по dto, передан тип: {type(dto)}'
        super().__init__(self.msg)