from pydantic import BaseModel, Field
from app.shared.dto.enums import RoleEnum


class UpdateUserCommand(BaseModel):
    display_name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = Field(None, max_length=500)
    years_old: int | None = Field(None, ge=0, le=150)
    avatar_url: str | None = None


class ChangeRoleCommand(BaseModel):
    role: RoleEnum


class ChangePasswordCommand(BaseModel):
    old_password: str | None = None
    new_password: str = Field(..., min_length=8)