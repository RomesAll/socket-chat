from sqlalchemy import select
from sqlalchemy.orm import joinedload, selectinload
from app.data_layer.repositories.base import BaseRepository
from app.shared.dto.user import UserDtoUpdateDefaultInfo, UserDtoUpdateExtendedInfo
from app.data_layer.models import User, UserInfo


class UserRepository(BaseRepository[User]):
    """Репозиторий для работы с данными пользователя"""
    MODEL = User
    USER_INFO_MODEL = UserInfo

    async def get_users(self, with_relation: bool = False) -> list[User]:
        """Получение списка пользователей"""
        options = None
        if with_relation:
            options = self._with_user_options()
        result = await self._get(options)
        return result

    async def get_user_by_id(self, user_id: str, with_relation: bool = False) -> User:
        """Получение пользователя по id"""
        options = None
        if with_relation:
            options = self._with_user_options()
        result = await self._get_by_id(user_id, options)
        return result

    async def get_user_by_email(self, email: str, with_relation: bool = False) -> UserInfo:
        """Получение пользователя по email"""
        stmt = (
            select(self.USER_INFO_MODEL)
            .where(self.USER_INFO_MODEL.email == email)
        )
        if with_relation:
            stmt = stmt.options(*self._with_user_info_options())
        sqla_obj = await self.session.execute(stmt)
        user_info = sqla_obj.scalar_one_or_none()
        if not user_info:
            raise Exception
        return user_info

    async def update_default_info(self, user_id, update_user: UserDtoUpdateDefaultInfo) -> User:
        """Обновления пользователя"""
        result = await self.update(user_id, update_user)
        return result

    async def update_extended_info(self, user_id, update_user: UserDtoUpdateExtendedInfo) -> UserInfo:
        """Обновление расширенной информации о пользователе"""
        user = await self.get_user_by_id(user_id, True)
        raw_data = update_user.model_dump(
            exclude_none=True,
            exclude_unset=True,
            exclude_defaults=True
        )
        for k, v in raw_data.items():
            setattr(user.user_info, k, v)
        return user.user_info

    def _with_user_options(self):
        """Получение relation для жадной загрузки"""
        return [
            joinedload(self.MODEL.user_info),
            selectinload(self.MODEL.room_members),
            selectinload(self.MODEL.owned_rooms)
        ]

    def _with_user_info_options(self):
        """Получение relation для жадной загрузки"""
        return [
            joinedload(self.USER_INFO_MODEL.user)
        ]