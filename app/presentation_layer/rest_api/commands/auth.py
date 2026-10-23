from pydantic import BaseModel, EmailStr, Field


class RegisterCommand(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=100)
    display_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8)


class LoginCommand(BaseModel):
    user_id: str
    password: str


class VerifyCodeCommand(BaseModel):
    user_id: str
    code: int


class RefreshTokenCommand(BaseModel):
    refresh_token: str