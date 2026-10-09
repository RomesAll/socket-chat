from datetime import datetime, timezone
from sqlalchemy import select
from app.data_layer.exceptions import RecordNotFound
from app.data_layer.repositories.base.base_repo import (
    BaseGetRepository,
    BaseSaveRepository,
    BaseUpdateRepository,
    BaseDeleteRepository
)
from app.shared.dto.user import UserEncryptedSaveDTO, UserUpdateDTO
from app.data_layer.models import User


class UserRepository(
    BaseGetRepository[User],
    BaseSaveRepository[User, UserEncryptedSaveDTO],
    BaseUpdateRepository[User, UserUpdateDTO],
    BaseDeleteRepository[User]
):
    """Репозиторий для работы с данными пользователя"""

    MODEL: type[User] = User

    async def get_user_by_email(self, email: str) -> User:
        """
        Получить пользователя по email.
        :param email: Почта.
        :return: Объект orm модели User.
        """
        stmt = (
            select(self.MODEL)
            .where(self.MODEL.email == email)
        )
        user_info = await self.session.scalar(stmt)
        if not user_info:
            raise RecordNotFound([email], self.MODEL.__tablename__, 'email')
        return user_info

    async def change_email(self, user_id: str, new_email: str) -> User:
        """
        Сменить адрес электронной почты.

        :param user_id: Id пользователя.
        :param new_email: Новая почта.
        :return: Объект orm модели User.
        """
        user_info = await self.get_record_by_id(user_id)
        user_info.email = new_email
        await self.session.flush()
        return user_info

    async def change_password(self, user_id: str, hash_psw: bytes) -> User:
        """
        Сменить адрес электронной почты.

        :param user_id: Id пользователя.
        :param hash_psw: Хеш пароля.
        :return: Объект orm модели User.
        """
        user_info = await self.get_record_by_id(user_id)
        user_info.password = hash_psw
        await self.session.flush()
        return user_info

    async def soft_delete(self, user_id: str) -> User:
        """
        Мягкое удаление пользователя с возможностью восстановления.

        :param user_id: Id пользователя.
        :return: Объект orm модели User.
        """
        user_info = await self.get_record_by_id(user_id)
        user_info.is_deleted = True
        user_info.deleted_at = datetime.now(tz=timezone.utc)
        await self.session.flush()
        return user_info

    async def recovery_delete(self, user_id: str) -> User:
        """
        Восстановление удаленного пользователя
        :param user_id: id пользователя
        :return: объект orm модели User
        """
        user_info = await self.get_record_by_id(user_id)
        user_info.is_deleted = False
        user_info.deleted_at = None
        await self.session.flush()
        return user_info