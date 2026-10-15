from uuid import UUID
from app.infrastructure.database.exceptions import RecordNotFound
from app.infrastructure.database.models import ChatMember
from app.infrastructure.database.repositories.base import BaseSaveRepository
from app.shared.dto.chat import ChatMemberSaveDTO
from app.shared.dto.enums import ChatRole


class ChatMemberRepository(
    BaseSaveRepository[ChatMember, ChatMemberSaveDTO],
):
    """Репозиторий для записи участников чата."""

    MODEL: type[ChatMember] = ChatMember

    async def get_by_ids(self, chat_id: UUID, user_id: str) -> ChatMember:
        """Участник по составному ключу. Кидает RecordNotFound."""
        member = await self.session.get(self.MODEL, (chat_id, user_id))
        if member is None:
            raise RecordNotFound(
                [chat_id, user_id],
                self.MODEL.__tablename__,
                'chat_id, user_id',
            )
        return member

    async def find_by_ids(self, chat_id: UUID, user_id: str) -> ChatMember | None:
        """Участник по составному ключу или None."""
        return await self.session.get(self.MODEL, (chat_id, user_id))

    async def set_role(self, chat_id: UUID, user_id: str, role: ChatRole) -> ChatMember:
        """Поменять роль участника."""
        member = await self.get_by_ids(chat_id, user_id)
        member.role = role
        await self.session.flush()
        return member

    async def set_mute(self, chat_id: UUID, user_id: str, mute: bool) -> ChatMember:
        """Включить или выключить mute."""
        member = await self.get_by_ids(chat_id, user_id)
        member.mute = mute
        await self.session.flush()
        return member

    async def set_last_read(
        self, chat_id: UUID, user_id: str, message_id: UUID | None,
    ) -> ChatMember:
        """Обновить last_read_message_id."""
        member = await self.get_by_ids(chat_id, user_id)
        member.last_read_message_id = message_id
        await self.session.flush()
        return member

    async def remove(self, chat_id: UUID, user_id: str) -> ChatMember:
        """Удалить участника из чата."""
        member = await self.get_by_ids(chat_id, user_id)
        await self.session.delete(member)
        await self.session.flush()
        return member