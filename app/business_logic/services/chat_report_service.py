from uuid import UUID
from app.domain.events import ChatMemberAdded, ChatMemberRemoved
from app.infrastructure.mongo.analytics.repositories import ChatAnalyticsRepository
from app.shared.dto.reports import ChatChangeOwner
from app.shared.log_config import LogMixin


class ChatReportService(LogMixin):
    """Сервис для управления отчетами комнат"""

    def __init__(self, chat_repo: ChatAnalyticsRepository):
        self._repo = chat_repo

    async def get_added_member(self, chat_id: UUID, days: int = 30) -> list[ChatMemberAdded]:
        """Получить список добавлены участников чата за N дней"""
        results = await self._repo.get_added_member(chat_id, days)
        self.log_debug(f"get_added_member: получено {len(results)} записей")
        return [ChatMemberAdded(**res) for res in results]

    async def get_removed_member(self, chat_id: UUID, days: int = 30) -> list[ChatMemberRemoved]:
        """Получить список удаленных участников чата за N дней"""
        results = await self._repo.get_removed_member(chat_id, days)
        self.log_debug(f"get_removed_member: получено {len(results)} записей")
        return [ChatMemberRemoved(**res) for res in results]

    async def get_changed_owner(self, chat_id: UUID) -> list[ChatChangeOwner]:
        """Получить список владельцев чата"""
        results = await self._repo.find_changed_owner(chat_id)
        self.log_debug(f"get_changed_owner: получено {len(results)} записей")
        return [ChatChangeOwner(**res) for res in results]