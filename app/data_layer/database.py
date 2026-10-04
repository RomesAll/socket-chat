from contextlib import contextmanager
import mongotic.asyncio as mongotic_async
import sqlalchemy.ext.asyncio as sqlalchemy_async


class SQLDatabase:
    """Класс для управления подключением к бд для SQLAlchemy"""
    def __init__(self, url: str):
        self.engine = sqlalchemy_async.create_async_engine(url=url)
        self.session_factory = sqlalchemy_async.async_sessionmaker(self.engine)

    @contextmanager
    def get_session(self):
        """Получение сессии в контекстном менеджере"""
        session = self.session_factory()
        try:
            yield session
            session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.close()

    def create_session(self) -> sqlalchemy_async.AsyncSession:
        """Прямое получение сессии"""
        return self.session_factory()


class MongoticDatabase:
    """Класс для управления подключением к бд для Mongodb"""
    def __init__(self, url: str):
        self.engine = mongotic_async.create_async_engine(host=url)
        self.session_factory = mongotic_async.async_sessionmaker(self.engine)

    @contextmanager
    def get_session(self):
        """Получение сессии в контекстном менеджере"""
        session = self.session_factory()
        try:
            yield session
            session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.close()

    def create_session(self) -> mongotic_async.AsyncSession:
        """Прямое получение сессии"""
        return self.session_factory()