from dataclasses import is_dataclass, fields
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import TypeVar, Generic, Any, Sequence
from app.infrastructure.database.exceptions import RecordNotFound
from app.infrastructure.database.models import Base
from app.infrastructure.database.repositories.metaclass_repo import RepoMeta
from app.shared.dto.base import BaseSaveDTO, BaseUpdateDTO, UNSET

TUpdateDto = TypeVar("TUpdateDto", bound=BaseUpdateDTO)
TSaveDto = TypeVar("TSaveDto", bound=BaseSaveDTO)
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
    Базовый класс репозитория для создания записей.

    DTO — dataclass. Поля со значением UNSET пропускаются,
    чтобы БД применила свои default-значения.
    """

    async def save(self, request: TSaveDto) -> TOrmModel:
        if not is_dataclass(request):
            raise TypeError(
                f"{type(request).__name__} объект должен быть dataclass"
            )

        data = {
            f.name: getattr(request, f.name)
            for f in fields(request)
            if getattr(request, f.name) is not UNSET
        }

        orm_model = self.MODEL(**data)
        self.session.add(orm_model)
        await self.session.flush()
        await self.session.refresh(orm_model)
        return orm_model


class BaseUpdateRepository(BaseRepository[TOrmModel], Generic[TOrmModel, TUpdateDto]):
    """
    Базовый класс репозитория для обновления записей.

    DTO — dataclass. Поля со значением UNSET не трогают запись,
    поля со значением None — явно обнуляют колонку.
    """

    async def update(self, record_id: Any, request: TUpdateDto) -> TOrmModel:
        if not is_dataclass(request):
            raise TypeError(f"{type(request).__name__} объект должен быть dataclass")

        record_info: TOrmModel | None = await self.session.get(self.MODEL, record_id)

        if record_info is None:
            raise RecordNotFound([record_id], self.MODEL.__tablename__, 'id')

        update_raw = request.get_not_null_attrs()

        if not update_raw:
            return record_info

        for key, val in update_raw.items():
            setattr(record_info, key, val)

        await self.session.flush()
        await self.session.refresh(record_info)
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