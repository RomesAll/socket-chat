from sqlalchemy.ext.asyncio import AsyncSession
from app.data_layer.repositories import MessageRepository, ChatRepository, RoomRepository, UserRepository


class UnitOfWork:
    """Паттерн unit of work (асинхронный)"""
    def __init__(self, session: AsyncSession):
        self.session = session
        self.msg_repo = MessageRepository(self.session)
        self.chat_repo = ChatRepository(self.session)
        self.room_repo = RoomRepository(self.session)
        self.user_repo = UserRepository(self.session)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        try:
            if exc_type:
                await self.session.rollback()
            else:
                await self.session.commit()
        finally:
            await self.session.close()