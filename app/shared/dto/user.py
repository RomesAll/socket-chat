from datetime import datetime
from pydantic import BaseModel, model_validator
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
    email: str
    password: bytes
    repeat_password: bytes

    @model_validator(mode='after')
    def validate_psw(self):
        if self.repeat_password != self.password:
            raise ValueError('Пароли не совпадают')
        return self


class UserDtoUpdateDefaultInfo(BaseModel):
    """DTO для хранения и валидации информации об обновлении сущ. пользователя"""
    display_name: str | None = None
    avatar_url: str | None = None


class UserDtoUpdateExtendedInfo(BaseModel):
    """DTO для обновления расширенной информации о пользователе"""
    description: str | None = None
    years_old: int | None = None
    role: RoleEnum | None = None


class UserInfoCache(BaseModel):
    """DTO для сохранения инф. о пользователе в кещ"""
    id: str
    display_name: str
    avatar_url: str
    years_old: int
    role: RoleEnum
    email: str
    created_at: datetime
    updated_at: datetime


class UserDtoBriefGet(BaseModel):
    """DTO для получения общей информации о пользователе"""
    id: str
    display_name: str
    avatar_url: str | None = None
    description: str | None = None
    years_old: int | None = None



class UserDtoGet(UserDtoBriefGet):
    """DTO для получения информации о пользователе"""
    role: RoleEnum
    email: str
    created_at: datetime
    updated_at: datetime


class RegisterDtoGet(UserDtoGet):
    """DTO для получения ответа после регистрации"""
    code: int | None = None