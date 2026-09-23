from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import TypeVar, Generic, Any
from app.data_layer.models import Base, Room, RoomMember, User, UserInfo
from app.shared.dto.room import RoomDtoSave, RoomMemberDtoSave
from app.shared.dto.user import UserDtoSave, UserDtoInfoSave

TOrmModel = TypeVar('TOrmModel', bound=Base)


class BaseRepository(Generic[TOrmModel]):
    MODEL: type[Base] = Base
    MAPPING_DTO_ORM_SAVE = {
        RoomDtoSave: Room,
        RoomMemberDtoSave: RoomMember,
        UserDtoSave: User,
        UserDtoInfoSave: UserInfo
    }

    def __init__(self, session: AsyncSession):
        self.session = session

    @classmethod
    def dto_to_orm(cls, dto: BaseModel) -> TOrmModel:
        """
        Конвертация из dto модели в orm объекты с учетом вложенных
        атрибутов. Обход вложенных атрибутов осуществляется через рекурсию.

        Алгоритм:\n
        - Проверяем что переданный dto это объект pydantic
        - С помощью маппинга получаем orm модель для типа pydantic (если нет, то ошибка)
        - Формирует результирующую коллекцию raw_data
        - Итерируемся по атрибутам dto
        - На каждой итерации получаем значение атрибута и проверяем
        - Если атрибут не коллекция, то просто добавляем как есть в raw_data
        - Если атрибут коллекция, то для него вызываем нашу функцию рекурсивно и передаем вложенную коллекцию
        - В результате рекурсивный алгоритм создает orm объект по raw_data и возвращает его вверх по рекурсии
        :param dto:
        :return:
        """
        if not isinstance(dto, BaseModel):
            raise Exception
        model = cls.MAPPING_DTO_ORM_SAVE.get(type(dto), None)
        if not model:
            raise Exception
        raw_data = {}
        for field in dto.model_fields.keys():
            value = getattr(dto, field)
            if isinstance(value, (list, tuple, set, BaseModel)):
                orm_nested = None
                if isinstance(value, BaseModel):
                    orm_nested = cls.dto_to_orm(value)
                elif isinstance(value, (list, tuple, set)):
                    orm_nested = [cls.dto_to_orm(record) for record in value]
                raw_data[field] = orm_nested
            else:
                raw_data[field] = value
        orm_model = model(**raw_data)
        return orm_model

    async def _get(self, relation: list | None = None) -> list[TOrmModel]:
        """Получение списка записей из бд"""
        stmt = select(self.MODEL)
        if relation:
            stmt = stmt.options(*relation)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def _get_by_id(self, record_id: Any, relation: list | None = None) -> TOrmModel:
        """Получение записи по id"""
        stmt = select(self.MODEL).where(self.MODEL.id == record_id)
        if relation:
            stmt = stmt.options(*relation)
        sqla_obj = await self.session.execute(stmt)
        result = sqla_obj.scalar_one_or_none()
        if not result:
            raise Exception
        return result

    async def save(self, request: BaseModel) -> TOrmModel:
        """Сохранение новой записи в бд"""
        orm_model = self.dto_to_orm(request)
        self.session.add(orm_model)
        await self.session.flush()
        return orm_model

    async def update(self, record_id: Any, request: BaseModel) -> TOrmModel:
        """Обновление существующей записи в бд"""
        record_info = await self._get_by_id(record_id)
        raw_data = request.model_dump(
            exclude_none=True,
            exclude_unset=True,
            exclude_defaults=True
        )
        for k, v in raw_data.items():
            setattr(record_info, k, v)
        return record_info

    async def delete(self, record_id: Any) -> TOrmModel:
        """Удаление записи из бд"""
        record_info = await self._get_by_id(record_id)
        await self.session.delete(record_info)
        return record_info