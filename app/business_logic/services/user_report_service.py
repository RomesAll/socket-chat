from app.infrastructure.database.repositories import UserRepository
from app.infrastructure.mongo.analytics.repositories import UserAnalyticsRepository
from app.shared.dto.reports import CountCreatedUser, CountDeletedUser
from app.shared.log_config import LogMixin


class UserReportService(LogMixin):
    """Сервис для управления пользователями"""

    def __init__(self, user_analytics_repo: UserAnalyticsRepository, user_db_repo: UserRepository):
        self._user_analytics_repo = user_analytics_repo
        self._user_db_repo = user_db_repo

    async def get_count_created_by_day(self, days: int = 30) -> list[CountCreatedUser]:
        """Получить кол-во созданных пользователей за N дней"""
        results = await self._user_analytics_repo.count_created_by_day(days)
        self.log_debug(f"get_count_created_by_day: получено {len(results)} записей")
        return [CountCreatedUser(**res) for res in results]

    async def get_count_deleted_by_day(self, days: int = 30) -> list[CountDeletedUser]:
        """Получить кол-во удаленных пользователей за N дней"""
        results = await self._user_analytics_repo.count_deleted_by_day(days)
        self.log_debug(f"get_count_deleted_by_day: получено {len(results)} записей")
        return [CountDeletedUser(**res) for res in results]

    async def get_count_admin(self) -> int:
        """Получить кол-во админов"""
        return await self._user_db_repo.get_count_admin()

    async def get_count_user(self) -> int:
        """Получить кол-во пользователей"""
        return await self._user_db_repo.get_count_users()

    async def get_top_email_domain(self) -> dict[str, int]:
        """Получить самые популярные домены для email адресов"""
        return await self._user_db_repo.get_top_email_domain()