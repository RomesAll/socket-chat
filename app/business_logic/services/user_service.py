import random
from app.business_logic.psw_manager import PasswordManager
from app.business_logic.redis_adapter import VerifyCodeStorage, Cache
from app.data_layer.models.events import EventType
from app.business_logic.unit_of_work import UnitOfWork
from app.shared.dto import UserDtoSave
from app.shared.dto.user import UserDtoGet, UserDtoBriefGet
from app.shared.log_config import LogMixin
from app.shared.config import get_config, AppMode
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

    async def add_user(self, new_user: UserDtoSave) -> UserDtoGet:
        """
        Добавление нового пользователя, алгоритм:
        1) для переданного атрибута new_user.user_info.password высчитывается хеш;
        2) сохраняет хеш в new_user.user_info.password;
        3) генерируется соде для подтверждения;
        4) сохраняется в бд;
        5) регистрируется событие NEW_USER для последующей отправки кода на почту;
        6) сохраняется информация о пользователе в кеш (после успешного commit).
        :param new_user: DTO для создания нового пользователя
        :return:
        """
        async with self._uow as uow:
            hash_psw = self._psw_manager.hash_password(new_user.user_info.password)
            new_user.user_info.password = hash_psw
            user_orm = await uow.user_repo.save(new_user)
            self.log_info(f'Пользователь {new_user.id} успешно сохранен в БД')
            code = random.randint(10000, 99999)
            await self._verify_code_storage.save(user_orm.id, code)
            response = UserDtoGet(**user_orm)
            if config.mode not in (AppMode.DEV, ):
                uow.add_event(
                    event_name='Save new user',
                    payload=response,
                    event_type=EventType.NEW_USER
                )
                self.log_info(f'Событие NEW_USER зарегистрировано для пользователя {new_user.id}')
        is_saved = await self._cache.save_user_info(user_info=UserDtoBriefGet(**user_orm))
        if not is_saved:
           self.log_warning(f'Пользователь {new_user.id} не был сохранен в кеше')
        return response