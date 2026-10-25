from dataclasses import dataclass
from uuid import UUID
from app.shared.dto.chat import ChatDTO
from app.shared.dto.enums import ChatRole


@dataclass(frozen=True)
class ChatAdded:
    chat: ChatDTO


@dataclass(frozen=True)
class ChatInvalidate:
    chat_id: UUID


@dataclass(frozen=True)
class ChatMemberAdded:
    """Участник добавлен в чат."""
    chat_id: UUID
    user_id: str
    role: ChatRole


@dataclass(frozen=True)
class ChatMemberRemoved:
    """Участник удалён из чата."""
    chat_id: UUID
    user_id: str


@dataclass(frozen=True)
class ChatMemberRoleChanged:
    """Роль участника чата изменена."""
    chat_id: UUID
    user_id: str
    old_role: ChatRole
    new_role: ChatRole


@dataclass(frozen=True)
class ChatOwnershipTransferred:
    """Владение чатом передано."""
    chat_id: UUID
    from_user: str
    to_user: str