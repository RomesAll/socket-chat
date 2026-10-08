from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import TypeVar, Generic, Any, Sequence
from app.data_layer.exceptions import RecordNotFound
from app.data_layer.models import Base
from app.data_layer.repositories.metaclass_repo import RepoMeta
from app.shared.dto.base import BaseSaveDto, BaseUpdateDto


TUpdateDto = TypeVar("TUpdateDto", bound=BaseUpdateDto)
TSaveDto = TypeVar("TSaveDto", bound=BaseSaveDto)
TOrmModel = TypeVar('TOrmModel', bound=Base)


class BaseRepository(Generic[TOrmModel], metaclass=RepoMeta):
    """
    Базовый класс репозитория.

    Определяет ORM модель, сохраняет асинхронную сессию базы данных и
    служит основой для специализированных CRUD репозиториев.
    """

    MODEL: type[TOrmModel]

    def __init__(self, session: AsyncSession):
        self.session = session


class BaseGetRepository(BaseRepository[TOrmModel]):
    """
    Базовый класс репозитория для чтения записей.

    Определяет базовый метод для получения записи по ID и списков объектов
    из базы данных с поддержкой пагинации
    """

    async def get_record_by_id(self, record_id: Any) -> TOrmModel:
        """
        Получить запись из базы данных по её уникальному идентификатору (ID).

        :param record_id: Идентификатор записи.
        :return: Объект ORM модели из базы данных.
        :raise RecordNotFound: Если запись с указанным ID не найдена в таблице.
        """
        result: TOrmModel | None = await self.session.get(self.MODEL, record_id)
        if result is None:
            raise RecordNotFound([record_id], self.MODEL.__tablename__, 'id')
        return result

    async def get_records(self, limit: int, offset: int) -> Sequence[TOrmModel]:
        """
        Получить список записей из базы данных с помощью пагинации.

        :param limit: Максимальное количество возвращаемых записей.
        :param offset: Количество записей, которое необходимо пропустить.
        :return: Список ORM моделей, обернутый в Sequence.
        """
        stmt = (
            select(self.MODEL)
            .order_by(self.MODEL.id)
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.scalars(stmt)
        return result.all()


class BaseSaveRepository(BaseRepository[TOrmModel], Generic[TOrmModel, TSaveDto]):
    """
    Базовый класс репозитория для создания записей в базе данных.

    Определяет стандартный метод для инициализации ORM-модели
    на основе переданного объекта DTO и её сохранения в сессии.
    """

    async def save(self, request: TSaveDto) -> TOrmModel:
        """
        Сохранить новую запись в базе данных.

        :param request: Объект DTO с валидированными данными для создания записи.
        :return: Созданный и добавленный в сессию объект ORM-модели.
        """
        # exclude_unset=True удаляет базовые значения pydantic,
        # для того, чтобы база данных применила свои базовые значения
        orm_model = self.MODEL(**request.model_dump(exclude_unset=True))
        self.session.add(orm_model)
        await self.session.flush()
        return orm_model


class BaseUpdateRepository(BaseRepository[TOrmModel], Generic[TOrmModel, TUpdateDto]):
    """
    Базовый класс репозитория для обновления записей в базе данных.

    Определяет стандартный метод для обновления существующей записи на
    основе переданного объекта DTO с валидированными данными.
    """

    async def update(self, record_id: Any, request: TUpdateDto) -> TOrmModel:
        """
        Обновить существующую запись в базе данных по
        идентификатору записи (ID).

        :param record_id: Идентификатор записи
        :param request: Объект DTO с валидированными данными для обновления записи.
        :return: Обновленная ORM-модель в сессии.
        :raise RecordNotFound: Если запись с указанным ID не найдена в таблице.
        """
        record_info: TOrmModel | None = await self.session.get(self.MODEL, record_id)
        if record_info is None:
            raise RecordNotFound([record_id], self.MODEL.__tablename__, 'id')
        raw_data = request.model_dump(exclude_unset=True)
        for k, v in raw_data.items():
            setattr(record_info, k, v)
        await self.session.flush()
        return record_info


class BaseDeleteRepository(BaseRepository[TOrmModel]):
    """
    Базовый класс репозитория для удаления записей из базы данных.

    Определяет стандартный метод для удаления записи по
    идентификатору записи (ID).
    """

    async def delete(self, record_id: Any) -> TOrmModel:
        """
        Удалить существующую запись из базы данных по ее
        уникальному идентификатору.

        :param record_id: Идентификатор записи.
        :return: Удаленная ORM-модель из сессии.
        """
        record_info: TOrmModel | None = await self.session.get(self.MODEL, record_id)
        if record_info is None:
            raise RecordNotFound([record_id], self.MODEL.__tablename__, 'id')
        await self.session.delete(record_info)
        await self.session.flush()
        return record_info