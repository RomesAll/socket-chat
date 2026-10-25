from app.infrastructure.database.models import Room
from app.shared.dto.room import RoomDTO


class RoomMapper:
    """Маппинг для агрегатов Room."""

    @staticmethod
    def to_dict(dto: RoomDTO) -> dict:
        """DTO модель комнаты -> python словарь"""
        return {
            'chat_id': dto.chat_id,
            'title': dto.title,
            'description': dto.description,
            'avatar_url': dto.avatar_url,
            'created_at': dto.created_at,
            'updated_at': dto.updated_at
        }

    @staticmethod
    def to_dto(room_orm: Room) -> RoomDTO:
        """Из ORM модели комнаты -> DTO модель."""
        return RoomDTO(
            chat_id=room_orm.chat_id,
            title=room_orm.title,
            description=room_orm.description,
            avatar_url=room_orm.avatar_url,
            created_at=room_orm.created_at,
            updated_at=room_orm.updated_at,
            max_users=room_orm.max_users
        )