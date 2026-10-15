from app.infrastructure.database.models import Chat, ChatMember
from app.shared.dto.chat import ChatDTO, ChatMemberDTO


class ChatMapper:
    """Маппинг для агрегатов Chat."""

    @staticmethod
    def chat_to_dict(dto: ChatDTO) -> dict:
        """DTO модель чата -> python словарь"""
        return {
            'id': dto.id,
            'type': dto.type,
            'is_active': dto.is_active,
            'last_message_at': dto.last_message_at,
            'created_at': dto.created_at,
            'updated_at': dto.updated_at
        }

    @staticmethod
    def chat_to_dto(chat_orm: Chat) -> ChatDTO:
        """Из ORM модели чата -> DTO модель."""
        return ChatDTO(
            id=chat_orm.id,
            type=chat_orm.type,
            is_active=chat_orm.is_active,
            last_message_at=chat_orm.last_message_at,
            created_at=chat_orm.created_at,
            updated_at=chat_orm.updated_at,
            last_message_id=chat_orm.last_message_id
        )

    @staticmethod
    def member_to_dict(dto: ChatMemberDTO) -> dict:
        """DTO модель участника -> python словарь"""
        return {
            'chat_id': dto.chat_id,
            'user_id': dto.user_id,
            'role': dto.role,
            'mute': dto.mute,
            'last_read_message_id': dto.last_read_message_id,
            'created_at': dto.created_at,
            'updated_at': dto.updated_at
        }

    @staticmethod
    def member_to_dto(member_orm: ChatMember) -> ChatMemberDTO:
        """Из ORM модели участника -> DTO модель."""
        return ChatMemberDTO(
            chat_id=member_orm.chat_id,
            user_id=member_orm.user_id,
            role=member_orm.role,
            mute=member_orm.mute,
            last_read_message_id=member_orm.last_read_message_id,
            created_at=member_orm.created_at,
            updated_at=member_orm.updated_at
        )