from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import TypeVar, Generic, Any, Sequence
from app.data_layer.exceptions import RecordNotFound
from app.data_layer.models import Base
from app.data_layer.repositories.metaclass_repo import RepoMeta


TOrmModel = TypeVar('TOrmModel', bound=Base)


class BaseRepository(Generic[TOrmModel], metaclass=RepoMeta):
    """Базовый репозиторий для работы с данными"""
    MODEL: type[Base] = Base

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_records(self, limit: int, offset: int) -> Sequence[TOrmModel]:
        """
        Получение из БД список записей с помощью пагинации
        :param limit: кол-во записей
        :param offset: пропустить кол-во записей
        :return: Sequence объекты orm модели sqlalchemy
        """
        stmt = (
            select(self.MODEL)
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.scalars(stmt)
        return result.all()

    async def get_record_by_id(self, record_id: Any) -> TOrmModel:
        """
        Получение из БД записи по уникальному идентификатору
        :param record_id: идентификатор записи
        :return: объект orm модели sqlalchemy
        """
        stmt = select(self.MODEL).where(self.MODEL.id == record_id)
        result = await self.session.scalar(stmt)
        if not result:
            raise RecordNotFound(record_id, self.MODEL.__tablename__, 'id')
        return result

    async def save(self, request: BaseModel) -> TOrmModel:
        """
        Сохранение новой записи в БД
        :param request: pydantic модель
        :return: сохраненный объект orm модели sqlalchemy
        """
        orm_model = self.MODEL(**request.model_dump())
        self.session.add(orm_model)
        await self.session.flush()
        return orm_model

    async def update(self, record_id: Any, request: BaseModel) -> TOrmModel:
        """
        Обновление существующей записи в БД
        :param record_id: идентификатор записи
        :param request: pydantic модель
        :return: обновленный объект orm модели sqlalchemy
        """
        record_info = await self.get_record_by_id(record_id)
        raw_data = request.model_dump(
            exclude_none=True,
            exclude_unset=True,
            exclude_defaults=True
        )
        for k, v in raw_data.items():
            setattr(record_info, k, v)
        await self.session.flush()
        return record_info

    async def delete(self, record_id: Any) -> TOrmModel:
        """
        Удаление существующей записи из БД
        :param record_id: идентификатор записи
        :return: удаленный объект orm модели sqlalchemy
        """
        record_info = await self.get_record_by_id(record_id)
        await self.session.delete(record_info)
        return record_info