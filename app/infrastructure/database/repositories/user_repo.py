from datetime import datetime, timezone
from typing import Sequence
from sqlalchemy import select, func, or_
from app.infrastructure.database.exceptions import RecordNotFound
from app.infrastructure.database.repositories.base.base_repo import (
    BaseGetRepository,
    BaseSaveRepository,
    BaseUpdateRepository,
    BaseDeleteRepository
)
from app.shared.dto.enums import RoleEnum
from app.shared.dto.user import UserEncryptedSaveDTO, UserUpdateDTO
from app.infrastructure.database.models import User


class UserRepository(
    BaseGetRepository[User],
    BaseSaveRepository[User, UserEncryptedSaveDTO],
    BaseUpdateRepository[User, UserUpdateDTO],
    BaseDeleteRepository[User]
):
    """Репозиторий для работы с данными пользователя"""

    MODEL: type[User] = User

    async def get_count_admin(self) -> int:
        """Получить кол-во админов."""
        stmt = (
            select(func.count())
            .select_from(self.MODEL)
            .where(or_(
                self.MODEL.role == RoleEnum.ADMIN,
                self.MODEL.role == RoleEnum.SUPER_ADMIN
            ))
        )
        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def get_count_users(self) -> int:
        """Получить кол-во пользователей"""
        stmt = (
            select(func.count())
            .select_from(self.MODEL)
        )
        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def get_top_email_domain(self) -> dict[str, int]:
        """Получить самые популярные домены для email адресов"""
        domain = func.split_part(self.MODEL.email, '@', 2).label('domain')
        count = func.count().label('count')

        stmt = (
            select(domain, count)
            .group_by(domain)
            .order_by(count.desc())
        )
        result = await self.session.execute(stmt)
        return {row.domain: row.count for row in result.all()}

    async def get_admins(self) -> Sequence[User]:
        """Получить список админов"""
        stmt = (
            select(self.MODEL)
            .where(self.MODEL.role.in_([RoleEnum.SUPER_ADMIN, RoleEnum.ADMIN]))
        )
        result = (await self.session.scalars(stmt)).all()
        return result

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

    async def change_role(self, user_id: str, new_role: RoleEnum):
        """Сменить роль пользователя."""
        user_info = await self.get_record_by_id(user_id)
        if user_info.role != new_role:
            user_info.role = new_role
            await self.session.flush()
            await self.session.refresh(user_info)
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