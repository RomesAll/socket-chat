from app.business_logic.services import ChatService
from app.infrastructure.redis import UnreadCache
from app.infrastructure.security import SymmetricEncode
from app.shared.dto.chat import GroupChatDTO
from app.shared.dto.message import MessageBriefGetDTO


class GetGroupChatsUseCase:
    """Получения групповых чатов"""

    def __init__(
            self,
            chat_service: ChatService,
            unread_cache: UnreadCache,
            encoder: SymmetricEncode
    ):
        self._chat_service = chat_service
        self._unread_cache = unread_cache
        self._encoder = encoder

    async def execute(self, user_id: str) -> list[GroupChatDTO]:
        chats = await self._chat_service.get_group_chats_preview(user_id)

        count_unread_msg = await self._unread_cache.get_all(user_id)

        result = []
        for chat in chats:
            last_msg = None
            if chat.last_message_id:
                last_msg = MessageBriefGetDTO(
                    type=chat.last_message_type,
                    sender_id=chat.last_message_sender_id,
                    text=self._encoder.decrypt(chat.last_message_body),
                    created_at=chat.last_message_created_at
                )

            result.append(GroupChatDTO(
                id=chat.id,
                title=chat.room_title,
                avatar_url=chat.room_avatar,
                last_message=last_msg,
                count_unread=count_unread_msg.get(str(chat.id), 0),
                role=chat.my_role
            ))

        return result