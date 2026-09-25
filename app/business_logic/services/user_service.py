import random
from app.business_logic.psw_manager import PasswordManager
from app.business_logic.redis_adapter import VerifyCodeStorage, Cache
from app.data_layer.models import User, UserInfo
from app.data_layer.models.events import EventType
from app.business_logic.unit_of_work import UnitOfWork
from app.shared.dto import UserDtoSave
from app.shared.dto.user import UserDtoGet, UserDtoBriefGet, RegisterDtoGet, UserDtoUpdateDefaultInfo, \
    UserDtoUpdateExtendedInfo
from app.shared.log_config import LogMixin
from app.shared.config import get_config, AppMode
from collections import deque
config = get_config()


class UserService(LogMixin):
    """Сервис для управления пользователями"""
    def __init__(
            self,
            uow: UnitOfWork,
            verify_code_storage: VerifyCodeStorage,
            psw_manager: type[PasswordManager],
            cache: Cache
    ):
        self._uow = uow
        self._verify_code_storage = verify_code_storage
        self._psw_manager = psw_manager
        self._cache = cache

    async def add_user(self, new_user: UserDtoSave) -> RegisterDtoGet:
        """
        Добавление нового пользователя, алгоритм:
        1) для переданного атрибута new_user.user_info.password высчитывается хеш;
        2) сохраняет хеш в new_user.user_info.password;
        3) генерируется соде для подтверждения;
        4) сохраняется в бд;
        5) регистрируется событие NEW_USER для последующей отправки кода на почту;
        6) сохраняется информация о пользователе в кеш (после успешного commit).
        :param new_user: DTO для создания нового пользователя
        :return: RegisterDtoGet (если режим работы DEV, то код подтверждения будет внутри модели)
        """
        async with self._uow as uow:
            hash_psw = self._psw_manager.hash_password(new_user.user_info.password)
            new_user.user_info.password = hash_psw
            user_orm = await uow.user_repo.save(new_user)
            self.log_info(f'Пользователь {new_user.id} успешно сохранен в БД')
            code = random.randint(10000, 99999)
            await self._verify_code_storage.save(user_orm.id, code)
            response = RegisterDtoGet(**user_orm)
            if config.mode not in (AppMode.DEV, ):
                uow.add_event(
                    event_name='Save new user',
                    payload=response,
                    event_type=EventType.NEW_USER
                )
                self.log_info(f'Событие NEW_USER зарегистрировано для пользователя {new_user.id}')
            else:
                response.code = code
        is_saved = await self._cache.save_user_info(user_info=UserDtoGet(**user_orm))
        if not is_saved:
           self.log_warning(f'Пользователь {new_user.id} не был сохранен в кеше')
        return response

    async def _get_users_info(
            self, limit: int, offset: int, with_relation: bool = False
    ) -> list[User]:
        """
        Получение информации о пользователях с возможностью получение связных записей
        (relationship)
        :param limit: кол-во записей
        :param offset: пропуск
        :param with_relation: выводить ли связанные записи
        :return: list[UserDtoBriefGet]
        """
        async with self._uow as uow:
            users = await uow.user_repo.get_users(limit, offset, with_relation)
            self.log_debug(f'Получение списка пользователей')
            return users

    async def get_users_brief_info(
            self, limit: int, offset: int, with_relation: bool = False
    ) -> list[UserDtoBriefGet]:
        """
        Получение краткой информации о пользователях с возможностью получение связных записей
        (relationship)
        :param limit: кол-во записей
        :param offset: пропуск
        :param with_relation: выводить ли связанные записи
        :return: list[UserDtoBriefGet]
        """
        users = await self._get_users_info(limit, offset, with_relation)
        response = [UserDtoBriefGet(**user.to_dict()) for user in users]
        return response

    async def get_users_extension_info(
            self, limit: int, offset: int, with_relation: bool = False
    ) -> list[UserDtoGet]:
        """
        Получение расширенной информации о пользователях с возможностью получение связных записей
        (relationship)
        :param limit: кол-во записей
        :param offset: пропуск
        :param with_relation: выводить ли связанные записи
        :return: list[UserDtoGet]
        """
        users = await self._get_users_info(limit, offset, with_relation)
        response = [UserDtoGet(**user.to_dict()) for user in users]
        return response

    async def _get_user_by_id(
            self, user_id: str, with_relation: bool = False
    ) -> dict:
        """
        Получение информации о пользователе с возможностью получение связных записей
        (relationship)
        :param user_id: id пользователя
        :param with_relation: выводить ли связанные записи
        :return: User
        """
        async with self._uow as uow:
            if not (user := await self._cache.get_user_info(user_id)):
                user = await uow.user_repo.get_user_by_id(user_id, with_relation)
                user = user.to_dict()
                self.log_debug(f'Получение информации о пользователе {user.id}')
            return user

    async def get_user_by_id_brief_info(
            self, user_id: str, with_relation: bool = False
    ) -> UserDtoBriefGet:
        """
        Получение краткой информации о пользователе с возможностью получение связных записей
        (relationship)
        :param user_id: id пользователя
        :param with_relation: выводить ли связанные записи
        :return: UserDtoBriefGet
        """
        user = await self._get_user_by_id(user_id, with_relation)
        response = UserDtoBriefGet(**user)
        return response

    async def get_user_by_id_extension_info(
            self, user_id: str, with_relation: bool = False
    ) -> UserDtoGet:
        """
        Получение расширенной информации о пользователе с возможностью получение связных записей
        (relationship)
        :param user_id: id пользователя
        :param with_relation: выводить ли связанные записи
        :return: UserDtoGet
        """
        user = await self._get_user_by_id(user_id, with_relation)
        response = UserDtoGet(**user)
        return response

    async def update_default_info_user(
            self, user_id, update_user: UserDtoUpdateDefaultInfo
    ) -> UserDtoGet:
        """
        Обновление базовой информации пользователя, алгоритм:
        1) сохраняет информацию в бд;
        2) регистрируется событие UPDATE_USER для последующего аудита;
        3) сохраняется информация о пользователе в кеш (после успешного commit).
        :param user_id: id пользователя
        :param update_user: DTO для хранения атрибутов для обновления
        :return:
        """
        async with self._uow as uow:
            user = await uow.user_repo.update_default_info(user_id, update_user)
            self.log_info(f'Обновлена информация о пользователе {user.id}')
            uow.add_event(
                event_name='Update user',
                payload=user.to_dict(),
                event_type=EventType.UPDATE_USER
            )
        is_saved = await self._cache.save_user_info(user_info=UserDtoGet(**user.to_dict()))
        if not is_saved:
            self.log_warning(f'Пользователь {user_id} не был сохранен в кеше')
        return UserDtoGet(**user.to_dict())

    async def update_extended_info_user(
            self, user_id, update_user: UserDtoUpdateExtendedInfo
    ) -> UserDtoGet:
        """
        Обновление расширенной информации пользователя, алгоритм:
        1) сохраняет информацию в бд;
        2) регистрируется событие UPDATE_USER для последующего аудита;
        3) сохраняется информация о пользователе в кеш (после успешного commit).
        :param user_id: id пользователя
        :param update_user: DTO для хранения атрибутов для обновления
        :return:
        """
        async with self._uow as uow:
            user = await uow.user_repo.update_extended_info(user_id, update_user)
            self.log_info(f'Обновлена информация о пользователе {user.id}')
            uow.add_event(
                event_name='Update user',
                payload=user.to_dict(),
                event_type=EventType.UPDATE_USER
            )
        is_saved = await self._cache.save_user_info(user_info=UserDtoGet(**user.to_dict()))
        if not is_saved:
            self.log_warning(f'Пользователь {user_id} не был сохранен в кеше')
        return UserDtoGet(**user.to_dict())

    async def delete_user(self, user_id: str) -> UserDtoGet:
        """
        Удаление информации о пользователе, алгоритм:
        1) удаляет информацию из бд;
        2) регистрируется событие DELETE_USER для последующего аудита;
        3) удаление пользователя из кеша.
        :param user_id: id пользователя
        :return:
        """
        async with self._uow as uow:
            user = await uow.user_repo.delete(user_id)
            self.log_info(f'Удалена информация о пользователе {user.id}')
            uow.add_event(
                event_name='Delete user',
                payload=user.to_dict(),
                event_type=EventType.DELETE_USER
            )
        is_saved = await self._cache.delete_user_info(str(user.id))
        if not is_saved:
            self.log_warning(f'Пользователь {user_id} не был удален из кеша')
        return UserDtoGet(**user.to_dict())