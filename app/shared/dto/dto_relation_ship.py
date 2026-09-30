from app.shared.dto import UserDtoBriefGet
from app.shared.dto.chat import ChatDtoGet, ChatMemberDtoGet
from app.shared.dto.room import RoomDtoGet, RoomMemberDtoGet
from app.shared.dto.user import UserDtoGet


class RoomDtoGetWithRelation(RoomDtoGet):
    """DTO для получения комнаты с relationship"""
    owner: UserDtoBriefGet
    members: list[RoomMemberDtoGet]
    chats: list[ChatDtoGet]


class RoomMemberDtoGetWithRelation(RoomMemberDtoGet):
    """DTO для получения участника комнаты с relationship"""
    room: RoomDtoGet
    user: UserDtoGet


class ChatDtoGetWithRelation(ChatDtoGet):
    """DTO для получения чата с relationship"""
    room: RoomDtoGet
    members: list[ChatMemberDtoGet]