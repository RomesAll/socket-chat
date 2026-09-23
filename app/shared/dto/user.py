from pydantic import BaseModel
from app.data_layer.models import RoleEnum


class UserDtoSave(BaseModel):
    """DTO для хранения и валидации информации о новом пользователе"""
    id: str
    display_name: str
    avatar_url: str | None = None
    user_info: UserDtoInfoSave


class UserDtoInfoSave(BaseModel):
    """DTO для хранения и валидации расширенной информации о новом пользователе"""
    id: str
    description: str | None = None
    years_old: int | None = None
    role: RoleEnum = RoleEnum.DEFAULT_USER
    email: str
    password: bytes


class UserDtoUpdateDefaultInfo(BaseModel):
    """DTO для хранения и валидации информации об обновлении сущ. пользователя"""
    display_name: str | None = None
    avatar_url: str | None = None


class UserDtoUpdateExtendedInfo(BaseModel):
    """DTO для обновления расширенной информации о пользователе"""
    description: str | None = None
    years_old: int | None = None
    role: RoleEnum | None = None