from dataclasses import asdict
from app.business_logic.mappers.user_mapper import UserMapper
from app.business_logic.unit_of_work import UnitOfWork
from app.domain.events import UserCreated, UserUpdated, UserPasswordChanged, UserDeleted
from app.infrastructure.redis import UserCache
from app.shared.dto.base import UNSET
from app.shared.dto.user import UserDtoGet, UserDtoBriefGet, UserUpdateDTO, UserEncryptedSaveDTO
from app.shared.log_config import LogMixin


class UserService(LogMixin):
    """
    Операции над агрегатом User.

    Инварианты:\n
    - Пароль хранится только в хешированном виде.
    - User ID уникален.
    - Email уникален.
    """

    def __init__(self, uow: UnitOfWork, mapper: UserMapper, cache: UserCache):
        self._uow = uow
        self._mapper = mapper
        self._cache = cache

    async def get(self, user_id: str) -> UserDtoGet:
        """Получить информацию о пользователе по ID."""
        cached = await self._cache.get(user_id)
        if cached:
            return cached
        user_orm = await self._uow.user_repo.get_record_by_id(user_id)
        return self._mapper.to_dto(user_orm)

    async def get_brief(self, user_id: str) -> UserDtoBriefGet:
        """Получить краткую информацию о пользователе по ID."""
        cached = await self._cache.get(user_id)
        if cached:
            return cached.to_brief()
        user_orm = await self._uow.user_repo.get_records(user_id)
        return self._mapper.to_dto_brief(user_orm)

    async def get_many(self, limit: int, offset: int) -> list[UserDtoGet]:
        """Получить информацию о пользователях с использованием пагинации."""
        user_many_orm = await self._uow.user_repo.get_records(limit, offset)
        result_dtos = [
            self._mapper.to_dto(user)
            for user in user_many_orm
        ]
        return result_dtos

    async def get_many_brief(self, limit: int, offset: int) -> list[UserDtoBriefGet]:
        """Получить информацию о пользователях с использованием пагинации."""
        user_many_ext_info = await self.get_many(limit, offset)
        return [user_dto.to_brief() for user_dto in user_many_ext_info]

    async def get_by_email(self, email: str) -> UserDtoGet:
        """Получить информацию о пользователе по email."""
        user_orm = await self._uow.user_repo.get_user_by_email(email)
        return self._mapper.to_dto(user_orm)

    async def save(self, user_dto: UserEncryptedSaveDTO) -> UserDtoGet:
        """
        Сохранить информацию о пользователе.

        Алгоритм:\n
        - Маппинг из DTO с открытым паролем -> DTO с захешированным.
        - Сохранение пользователя в сессию БД.
        - Маппинг в DTO из ORM.
        """
        user_orm = await self._uow.user_repo.save(user_dto)
        saved_user = self._mapper.to_dto(user_orm)
        self._uow.add_event(UserCreated(
            user=saved_user
        ))
        self.log_info(f"Создан пользователь {saved_user.id}")
        return saved_user

    async def update(self, user_id: str, user_dto: UserUpdateDTO) -> UserDtoGet:
        """
        Обновить информацию о пользователе.

        Алгоритм:\n
        - Сохранение обновленных данных в сессии БД.
        - Маппинг в DTO из ORM.
        """
        user_orm = await self._uow.user_repo.update(user_id, user_dto)
        updated_user = self._mapper.to_dto(user_orm)
        self._uow.add_event(UserUpdated(
            user=updated_user,
            changed_fields=[
                key for key, value in asdict(user_dto)
                if type(value) is not UNSET
            ]
        ))
        self.log_info(f"Обновлён пользователь {updated_user.id}")
        return updated_user

    async def update_password(self, user_id: str, new_psw: bytes) -> UserDtoGet:
        """
        Обновить пароль пользователя.

        Алгоритм:\n
        - Обновление информации в сессии БД.
        - Маппинг в DTO из ORM.
        """
        user_orm = await self._uow.user_repo.change_password(user_id, new_psw)
        updated_user = self._mapper.to_dto(user_orm)
        self._uow.add_event(UserPasswordChanged(
            user_id=user_id
        ))
        self.log_info(f"Обновлён пароль пользователя {updated_user.id}")
        return updated_user

    async def delete(self, user_id: str) -> UserDtoGet:
        """
        Удалить информацию о пользователе.

        Алгоритм:\n
        - Удаление информации из сессии БД.
        - Маппинг в DTO из ORM.
        """
        user_orm = await self._uow.user_repo.delete(user_id)
        deleted_user = self._mapper.to_dto(user_orm)
        self._uow.add_event(UserDeleted(
            user_id=user_id
        ))
        self.log_info(f"Удалён пользователь {deleted_user.id}")
        return deleted_user