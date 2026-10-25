from app.infrastructure.database.repositories import RoomReadRepository
from app.infrastructure.mongo.analytics.repositories import RoomAnalyticsRepository
from app.shared.dto.reports import CountCreatedRoom, CountDeletedRoom
from app.shared.dto.room import TopRoomsByMemberDTO
from app.shared.log_config import LogMixin


class RoomReportService(LogMixin):
    """Сервис для управления комнатами"""

    def __init__(self, chat_analytics_repo: RoomAnalyticsRepository, room_db_repo: RoomReadRepository):
        self._chat_analytics_repo = chat_analytics_repo
        self._room_db_repo = room_db_repo

    async def get_count_created_by_day(self, days: int = 30) -> list[CountCreatedRoom]:
        """Получить кол-во созданных комнат за N дней"""
        results = await self._chat_analytics_repo.count_created_by_day(days)
        self.log_debug(f"get_count_created_by_day: получено {len(results)} записей")
        return [CountCreatedRoom(**res) for res in results]

    async def get_count_deleted_by_day(self, days: int = 30) -> list[CountDeletedRoom]:
        """Получить кол-во удаленных комнат за N дней"""
        results = await self._chat_analytics_repo.count_deleted_by_day(days)
        self.log_debug(f"get_count_deleted_by_day: получено {len(results)} записей")
        return [CountDeletedRoom(**res) for res in results]

    async def top_rooms_by_member(self, top_count: int = 5) -> list[TopRoomsByMemberDTO]:
        """Поучить список комнат по наибольшему кол-ву участников"""
        return await self._room_db_repo.top_rooms_by_member(top_count)