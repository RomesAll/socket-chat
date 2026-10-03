import asyncio
from datetime import date
from uuid import UUID
from mongotic import select
from mongotic.asyncio import AsyncSession, create_async_engine
from app.data_layer.models.events import EventType, Status
from app.data_layer.models.statistics import UserStatistic, ChatStatistic
from app.shared.celery_app import celery_app
from app.shared.config import get_config
from typing import Callable


class StatisticManager:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_user_stat(self, user_id: str):
        user_stat = await self._session.scalar(
            select(UserStatistic)
            .where(UserStatistic.user_id == user_id)
        )
        return user_stat

    async def get_chat_stat(self, chat_id: UUID):
        chat_stat = await self._session.scalar(
            select(ChatStatistic)
            .where(ChatStatistic.chat_id == chat_id)
        )
        return chat_stat

    def get_handler_event(self, event_type: EventType) -> Callable:
        match event_type:
            case event_type.CREATE_NEW_USER:
                return self.create_new_user_event

            case event_type.DELETE_USER:
                return self.delete_user_event

            case event_type.SEND_ACTIVE_MONITOR_IN_USER:
                return self.send_active_monitor_in_user_event

            case event_type.SEND_DATE_USER_CONNECTION:
                return self.send_date_user_connection

            case event_type.SEND_MESSAGE_IN_CHAT:
                return self.send_message_in_chat_event

            case event_type.DELETE_MESSAGE_IN_CHAT:
                return self.delete_message_in_chat_event

            case event_type.DELETE_CHAT:
                return self.delete_chat_event

            case event_type.ADD_MEMBER_IN_CHAT:
                return self.add_member_in_chat_event

            case event_type.REMOVE_MEMBER_IN_CHAT:
                return self.remove_member_in_chat_event

            case event_type.SEND_ACTIVE_MONITOR_IN_CHAT:
                return self.send_active_monitor_in_chat_event

            case _: raise Exception

    async def create_new_user_event(self, payload: dict):
        user_stat = UserStatistic(user_id=payload['user_id'])
        self._session.add(user_stat)

    async def delete_user_event(self, payload: dict):
        user_stat = await self.get_user_stat(payload['user_id'])
        if not user_stat:
            return
        self._session.delete(user_stat)

    async def send_active_monitor_in_user_event(self, payload: dict):
        user_stat = await self.get_user_stat(payload['user_id'])
        last_active = user_stat.hourly_activity_pick
        user_stat.hourly_activity_pick = max(payload['time_active'], last_active)

    async def send_date_user_connection(self, payload: dict):
        user_stat = await self.get_user_stat(payload['user_id'])
        if not (last_connection := user_stat.last_connection):
            last_connection = date.fromisoformat(payload['date_connection'])
            user_stat.current_streak_days = 1
            user_stat.max_streak_days = 1
        date_connection = date.fromisoformat(payload['date_connection'])
        delta = date_connection - last_connection
        if delta.days == 1:
            user_stat.current_streak_days += 1
            user_stat.max_streak_days = max(
                user_stat.max_streak_days, user_stat.current_streak_days
            )
        elif delta.days >= 2:
            user_stat.current_streak_days = 0

    async def send_message_in_chat_event(self, payload: dict):
        user_stat = await self.get_user_stat(payload['user_id'])
        chat_stat = await self.get_chat_stat(payload['chat_id'])
        message_type = payload['message_type']
        if user_stat:
            user_stat.total_message += 1
            msg_by_type_new = dict(user_stat.messages_by_type)
            msg_by_type_new[message_type] = msg_by_type_new.get(message_type, 0) + 1
            user_stat.messages_by_type = msg_by_type_new
            if not user_stat.first_message_at:
                user_stat.first_message_at = date.today()
            user_stat.last_message_at = date.today().isoformat()
        if chat_stat:
            chat_stat.total_message += 1
            msg_by_type_new = dict(chat_stat.messages_by_type)
            msg_by_type_new[message_type] = msg_by_type_new.get(message_type, 0) + 1
            chat_stat.messages_by_type = msg_by_type_new

    async def delete_message_in_chat_event(self, payload: dict):
        user_stat = await self.get_user_stat(payload['user_id'])
        chat_stat = await self.get_chat_stat(payload['chat_id'])
        message_type = payload['message_type']
        if user_stat:
            user_stat.total_message -= 1
            user_stat.messages_by_type[message_type] = (
                    user_stat.messages_by_type.get(message_type, 1) - 1
            )
            if user_stat.total_message == 0:
                user_stat.first_message_at = None
            user_stat.last_message_at = None
        if chat_stat:
            chat_stat.total_message -= 1
            chat_stat.last_message_at = None
            chat_stat.messages_by_type[message_type] = (
                    chat_stat.messages_by_type.get(message_type, 1) - 1
            )

    async def create_new_chat_event(self, payload: dict):
        chat = ChatStatistic(chat_id=payload['chat_id'])
        self._session.add(chat)

    async def delete_chat_event(self, payload: dict):
        chat = ChatStatistic(chat_id=payload['chat_id'])
        self._session.delete(chat)

    async def add_member_in_chat_event(self, payload: dict):
        user_stat = await self.get_user_stat(payload['user_id'])
        chat_stat = await self.get_chat_stat(payload['chat_id'])
        user_stat.total_chats_count += 1
        chat_stat.count_users += 1

    async def remove_member_in_chat_event(self, payload: dict):
        user_stat = await self.get_user_stat(payload['user_id'])
        chat_stat = await self.get_chat_stat(payload['chat_id'])
        user_stat.total_chats_count -= 1
        chat_stat.count_users -= 1

    async def send_active_monitor_in_chat_event(self, payload: dict):
        chat_stat = await self.get_chat_stat(payload['chat_id'])
        new_dict = dict(chat_stat.hourly_activity_monitored)
        new_dict[payload['user_id']] = payload['time_active']
        chat_stat.hourly_activity_monitored = new_dict


@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=10,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
)
def update_statistics(self, type_action: str, payload: dict):
    """Celery задача для сохранения истории изменения объекта бд"""
    asyncio.run(_update_statistics(type_action, payload))


async def _update_statistics(type_action: str, payload: dict):
    engine = create_async_engine(get_config().mongodb.url)
    async with AsyncSession(bind=engine) as session:
        manager = StatisticManager(session)
        handler = manager.get_handler_event(EventType(type_action))
        await handler(payload)
        await session.commit()
    await engine.close()