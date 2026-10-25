from app.business_logic.services import ChatService
from app.infrastructure.redis import UnreadCache
from app.infrastructure.security import SymmetricEncode
from app.shared.dto.chat import PrivateChatDTO
from app.shared.dto.message import MessageBriefGetDTO
from app.shared.dto.enums import ChatType  # <-- ИМПОРТИРУЕМ ТИПЫ


class GetPrivateChatsUseCase:
    """Получение приватных чатов."""

    def __init__(
            self,
            chat_service: ChatService,
            unread_cache: UnreadCache,
            encoder: SymmetricEncode
    ):
        self._chat_service = chat_service
        self._unread_cache = unread_cache
        self._encoder = encoder

    async def execute(self, user_id: str) -> list[PrivateChatDTO]:
        chats = await self._chat_service.get_private_chats_preview(user_id)
        count_unread_msg = await self._unread_cache.get_all(user_id)

        result = []
        for chat in chats:
            if chat.type == ChatType.FAVORITES:
                companion_id = user_id
                companion_name = "Избранное (Вы)"
                companion_avatar = None
            else:
                companion_id = chat.other_user_id or user_id
                companion_name = chat.other_user_name or "Без имени"
                companion_avatar = chat.other_user_avatar

            last_msg = None
            if chat.last_message_id:
                last_msg = MessageBriefGetDTO(
                    type=chat.last_message_type,
                    sender_id=chat.last_message_sender_id,
                    text=self._encoder.decrypt(chat.last_message_body),
                    created_at=chat.last_message_created_at
                )

            result.append(PrivateChatDTO(
                id=chat.id,
                type=chat.type,
                companion_id=companion_id,
                companion_avatar=companion_avatar,
                companion_name=companion_name,
                last_message=last_msg,
                count_unread=count_unread_msg.get(str(chat.id), 0),
            ))

        return result