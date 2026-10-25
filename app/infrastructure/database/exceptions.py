from uuid import UUID
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
    """
    Запись не найдена в БД
    :param keys: значения, по которым ввелся поиск
    :param table: имя таблицы
    :param columns: имена колонок
    """
    def __init__(self, keys: list, table: str, columns: str):
        self.keys = keys
        self.table = table
        self.columns = columns
        super().__init__(f"{table} информация не найдена по {columns}={keys}")


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


class EmailSendError(Exception):
    """Ошибка отправки сообщения по почте."""
    def __init__(self, to: str, cause: str):
        self.to = to
        self.msg = f'Не удалось отправить сообщение на адрес: {to}, причина {cause}'
        super().__init__(self.msg)


class UserNotInRoomMember(Exception):
    """В комнате нет переданного участника."""
    def __init__(self, room_id: UUID, new_owner: str):
        self.room_id = room_id
        self.new_owner = new_owner
        self.msg = f'Пользователя {new_owner} нет в участниках комнаты {room_id}'
        super().__init__(self.msg)


class RemoveMemberInRoomPermDenied(Exception):
    """Ошибка удаление пользователя из комнаты."""
    def __init__(self, room_id: UUID, delete_user: str, actor_id: str):
        self.room_id = room_id
        self.delete_user = delete_user
        self.actor_id = actor_id
        self.msg = f'У пользователя {actor_id} недостаточно прав для удаления {delete_user} в комнате {room_id}'
        super().__init__(self.msg)


class DeleteRoomPermDenied(Exception):
    """Ошибка удаление комнаты."""
    def __init__(self, room_id: UUID, actor_id: str):
        self.room_id = room_id
        self.actor_id = actor_id
        self.msg = f'У пользователя {actor_id} нет прав на удаление комнаты {room_id}'
        super().__init__(self.msg)