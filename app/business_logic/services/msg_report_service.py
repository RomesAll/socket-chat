from uuid import UUID
from app.infrastructure.mongo.analytics.repositories import MessageAnalyticsRepository
from app.shared.dto.reports import TopChat, TopSender, MessageSent
from app.shared.log_config import LogMixin


class MessageReportService(LogMixin):
    """Сервис для управления отчетами сообщений"""

    def __init__(self, chat_repo: MessageAnalyticsRepository):
        self._repo = chat_repo

    async def get_count_msg_by_days(self, days: int = 30) -> list[MessageSent]:
        """Получить кол-во сообщений за N дней"""
        results = await self._repo.count_all_msg_send_by_days(days)
        self.log_debug(f"get_count_msg_by_days: получено {len(results)} записей")
        return [MessageSent(**res) for res in results]

    async def get_count_chat_msg_by_days(self, chat_id: UUID, days: int = 30) -> list[MessageSent]:
        """Получить кол-во сообщений за N дней в чате"""
        results = await self._repo.count_chat_msg_send_by_days(chat_id, days)
        self.log_debug(f"get_count_chat_msg_by_days: получено {len(results)} записей")
        return [MessageSent(**res) for res in results]

    async def get_top_chat(self) -> list[TopChat]:
        """Получить топ чатов по сообщениям"""
        results = await self._repo.top_chats()
        self.log_debug(f"get_top_chat: получено {len(results)} записей")
        return [TopChat(**res) for res in results]

    async def get_top_senders(self) -> list[TopSender]:
        """Получить топ отправителей по сообщениям"""
        results = await self._repo.top_senders()
        self.log_debug(f"get_top_senders: получено {len(results)} записей")
        return [TopSender(**res) for res in results]