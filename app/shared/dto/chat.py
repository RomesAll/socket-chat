from dataclasses import dataclass
from datetime import datetime
from uuid import UUID
from app.shared.dto.base import BaseSaveDTO, BaseUpdateDTO, UNSET, _UnsetType
from app.shared.dto.enums import ChatRole, ChatType


@dataclass(frozen=True, slots=True)
class ChatSaveDTO(BaseSaveDTO):
    """DTO для создания чата."""
    type: ChatType
    is_active: bool = True


@dataclass(frozen=True, slots=True)
class ChatUpdateDTO(BaseUpdateDTO):
    """DTO для обновления чата."""
    is_active: bool | None | _UnsetType = UNSET
    last_message_at: datetime | None | _UnsetType = UNSET


@dataclass(frozen=True, slots=True)
class ChatDTO:
    """DTO для получения базовой информации о чате"""
    id: UUID
    type: ChatType
    is_active: bool
    last_message_at: datetime | None


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
    last_read_message_id: UUID | None
    last_message_id: UUID | None