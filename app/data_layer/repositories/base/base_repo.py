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
    Базовый класс репозитория для определения модели, сохранения
    сессии и базовым методом получения записи по id
    """

    MODEL: type[TOrmModel]

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_record_by_id(self, record_id: Any) -> TOrmModel:
        """
        Получение из БД записи по уникальному идентификатору
        :param record_id: идентификатор записи
        :return: объект orm модели sqlalchemy
        """
        result: TOrmModel | None = await self.session.get(self.MODEL, record_id)
        if result is None:
            raise RecordNotFound([record_id], self.MODEL.__tablename__, 'id')
        return result


class BaseGetRepository(BaseRepository[TOrmModel]):
    """Базовый репозиторий для получения данных"""

    async def get_records(self, limit: int, offset: int) -> Sequence[TOrmModel]:
        """
        Получение из БД список записей с помощью пагинации
        :param limit: кол-во записей
        :param offset: пропустить кол-во записей
        :return: Sequence объекты orm модели sqlalchemy
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
    """Базовый репозиторий для сохранения данных"""

    async def save(self, request: TSaveDto) -> TOrmModel:
        """
        Сохранение новой записи в БД
        :param request: поля которые нужно сохранить
        :return: сохраненный объект orm модели sqlalchemy
        """
        orm_model = self.MODEL(**request.model_dump(exclude_unset=True))
        self.session.add(orm_model)
        await self.session.flush()
        return orm_model


class BaseUpdateRepository(BaseRepository[TOrmModel], Generic[TOrmModel, TUpdateDto]):
    """Базовый репозиторий для обновления данных"""

    async def update(self, record_id: Any, request: TUpdateDto) -> TOrmModel:
        """
        Обновление существующей записи в БД
        :param record_id: идентификатор записи
        :param request: поля которые нужно обновить
        :return: обновленный объект orm модели sqlalchemy
        """
        record_info: TOrmModel = await self.get_record_by_id(record_id)
        raw_data = request.model_dump(exclude_unset=True)
        for k, v in raw_data.items():
            setattr(record_info, k, v)
        await self.session.flush()
        return record_info


class BaseDeleteRepository(BaseRepository[TOrmModel]):
    """Базовый репозиторий для удаления данных"""

    async def delete(self, record_id: Any) -> TOrmModel:
        """
        Удаление существующей записи из БД
        :param record_id: идентификатор записи
        :return: удаленный объект orm модели sqlalchemy
        """
        record_info: TOrmModel = await self.get_record_by_id(record_id)
        await self.session.delete(record_info)
        await self.session.flush()
        return record_info