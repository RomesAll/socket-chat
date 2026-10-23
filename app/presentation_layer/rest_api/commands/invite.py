from pydantic import BaseModel, Field


class GenerateInviteCommand(BaseModel):
    hours: int = Field(24, ge=1, le=720)          # 1 час – 30 дней
    max_uses: int | None = Field(None, ge=1, le=10000)


class JoinByInviteCommand(BaseModel):
    token: str = Field(..., min_length=1, max_length=500)