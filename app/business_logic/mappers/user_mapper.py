from app.infrastructure.database.models import User
from app.shared.dto.user import UserDtoGet, UserDtoBriefGet


class UserMapper:
    """Маппинг для агрегатов User."""

    @staticmethod
    def to_dict(dto: UserDtoGet) -> dict:
        """DTO модель -> python словарь"""
        return {
            'id': dto.id,
            'display_name': dto.display_name,
            'avatar_url': dto.avatar_url,
            'created_at': dto.created_at,
            'updated_at': dto.updated_at,
            'description': dto.description,
            'years_old': dto.years_old,
            'role': dto.role,
            'email': dto.email,
            'last_seen_at': dto.last_seen_at,
        }

    @staticmethod
    def to_dto(user_orm: User) -> UserDtoGet:
        """Из ORM модели -> DTO модель."""
        return UserDtoGet(
            id=user_orm.id,
            display_name=user_orm.display_name,
            avatar_url=user_orm.avatar_url,
            created_at=user_orm.created_at,
            updated_at=user_orm.updated_at,
            description=user_orm.description,
            years_old=user_orm.years_old,
            role=user_orm.role,
            email=user_orm.email,
            last_seen_at=user_orm.last_seen_at,
        )

    @staticmethod
    def to_dto_brief(user_orm: User) -> UserDtoBriefGet:
        """Из ORM модели -> DTO модель с краткой информацией."""
        return UserDtoBriefGet(
            id=user_orm.id,
            display_name=user_orm.display_name,
            avatar_url=user_orm.avatar_url,
            created_at=user_orm.created_at,
            updated_at=user_orm.updated_at,
        )