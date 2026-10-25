from dataclasses import dataclass
from datetime import datetime
from uuid import UUID
from app.shared.dto.base import BaseSaveDTO, BaseUpdateDTO, UNSET, _UnsetType
from app.shared.dto.enums import ChatRole, ChatType
from app.shared.dto.message import MessageBriefGetDTO


@dataclass(frozen=True, slots=True)
class ChatSaveDTO(BaseSaveDTO):
    """DTO для создания чата."""
    id: UUID
    type: ChatType
    is_active: bool = True


@dataclass(frozen=True, slots=True)
class ChatUpdateDTO(BaseUpdateDTO):
    """DTO для обновления чата."""
    is_active: bool | None | _UnsetType = UNSET
    last_message_at: datetime | None | _UnsetType = UNSET
    last_message_id: UUID | None | _UnsetType = UNSET


@dataclass(frozen=True, slots=True)
class ChatDTO:
    """DTO для получения базовой информации о чате"""
    id: UUID
    type: ChatType
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_message_at: datetime | None = None
    last_message_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class PrivateChatDTO:
    id: UUID
    type: ChatType
    companion_id: str
    companion_name: str
    count_unread: int
    companion_avatar: str | None = None
    last_message: 'MessageBriefGetDTO | None' = None


@dataclass(frozen=True, slots=True)
class GroupChatDTO:
    id: UUID
    title: str
    last_message: 'MessageBriefGetDTO | None'
    count_unread: int
    role: ChatRole
    avatar_url: str | None = None


@dataclass(frozen=True, slots=True)
class ChatMemberSaveDTO(BaseSaveDTO):
    """DTO для добавления участника в чат."""
    chat_id: UUID
    user_id: str
    role: ChatRole = ChatRole.MEMBER
    mute: bool = False


@dataclass(frozen=True, slots=True)
class ChatMemberUpdateDTO(BaseUpdateDTO):
    """DTO для обновления участника чата."""
    role: ChatRole | None | _UnsetType = UNSET
    mute: bool | None | _UnsetType = UNSET
    last_read_message_id: UUID | None | _UnsetType = UNSET


@dataclass(frozen=True, slots=True)
class ChatMemberDTO:
    """DTO для получения информации об участниках чата"""
    chat_id: UUID
    user_id: str
    role: ChatRole
    mute: bool
    created_at: datetime
    updated_at: datetime
    last_read_message_id: UUID | None = None