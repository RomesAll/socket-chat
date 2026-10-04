from app.business_logic.psw_manager import PasswordManager
from app.business_logic.services import UserService
from app.business_logic.unit_of_work import UnitOfWork
from bootstrap import get_bootstrap


bootstrap = get_bootstrap()


def get_user_service() -> UserService:
    user_service = UserService(
        uow=UnitOfWork(
            sql_session=bootstrap.postgres_db.create_session(),
            mongo_session=bootstrap.mongo_db.create_session()
        ),
        verify_code_storage=bootstrap.verify_code_storage,
        psw_manager=PasswordManager,
        cache=bootstrap.cache,
        jwt_facade=bootstrap.jwt_facade,
        jwt_white_list=bootstrap.jwt_white_list,
        session_key_storage=bootstrap.session_key_storage,
        user_connections=bootstrap.ws_manager
    )
    return user_service