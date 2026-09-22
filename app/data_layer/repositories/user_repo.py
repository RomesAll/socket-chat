from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload, selectinload
from app.shared.dto.user import UserDtoSave, UserDtoUpdate
from app.data_layer.models import *


class UserRepository:
    USER_MODEL = User
    USER_INFO_MODEL = UserInfo

    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, user_save: UserDtoSave) -> User:
        """
        Сохранение информации о пользователе в БД
        :param user_save: dto объект
        :return:
        """
        user_info = user_save.user_info.model_dump(exclude_none=True)
        user = self.USER_MODEL(
            id=user_save.id,
            display_name=user_save.display_name,
            avatar_url=user_save.avatar_url,
            user_info=self.USER_INFO_MODEL(**user_info)
        )
        self.session.add(user)
        await self.session.flush()
        return user

    async def update(self, user_id: str, user_update: UserDtoUpdate) -> User:
        """
        Обновление информации о пользователе в БД
        :param user_id: id пользователя
        :param user_update: dto объект
        :return:
        """
        update_data = user_update.model_dump(
            exclude_none=True, exclude_unset=True, exclude_defaults=True
        )
        user = await self.get_by_id(user_id, True)
        self._update(update_data, user)
        self._update(update_data, user.user_info)
        return user

    @staticmethod
    def _update(update_data: dict, user: Base | None = None):
        """Обновление атрибутов дочерних объектов Base, без учета вложенных"""
        if not user:
            raise Exception
        user_columns = user.__table__.columns.keys()
        for col, val in update_data.items():
            if col in user_columns:
                setattr(user, col, val)

    async def delete(self, user_id: str) -> User:
        """
        Удаление пользователя из БД
        :param user_id: id пользователя
        :return:
        """
        user = await self.get_by_id(user_id, True)
        await self.session.delete(user)
        return user

    async def get(self, with_relation: bool = False) -> list[User]:
        """
        Получение списка пользователей из БД
        :param with_relation: включать ли relationship (делает доп. запросы)
        :return:
        """
        stmt = select(self.USER_MODEL)
        if with_relation:
            stmt = stmt.options(
                joinedload(self.USER_MODEL.user_info),
                selectinload(self.USER_MODEL.room_members),
                selectinload(self.USER_MODEL.owned_rooms),
            )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, user_id: str, with_relation: bool = False) -> User:
        """
        Получение информации о пользователе по id
        :param user_id: id пользователя
        :param with_relation: включать ли relationship (делает доп. запросы)
        :return:
        """
        stmt = select(self.USER_MODEL).where(self.USER_MODEL.id == user_id)
        if with_relation:
            stmt = stmt.options(
                joinedload(self.USER_MODEL.user_info),
                selectinload(self.USER_MODEL.room_members),
                selectinload(self.USER_MODEL.owned_rooms),
            )
        result = await self.session.execute(stmt)
        user = result.scalar_one_or_none()
        if not user:
            raise Exception
        return user

    async def get_by_email(self, user_email: str, with_relation: bool = False) -> UserInfo:
        """
        Получение информации о пользователе по email
        :param user_email: email пользователя
        :param with_relation: включать ли relationship (делает доп. запросы)
        :return:
        """
        stmt = select(self.USER_INFO_MODEL).where(self.USER_INFO_MODEL.email == user_email)
        if with_relation:
            stmt = stmt.options(
                joinedload(self.USER_MODEL.user_info),
            )
        result = await self.session.execute(stmt)
        user = result.scalar_one_or_none()
        if not user:
            raise Exception
        return user