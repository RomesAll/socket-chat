from pydantic import BaseModel, Field


class CreateRoomCommand(BaseModel):
    title: str
    description: str | None = None
    max_users: int = 30


class RoomUpdateCommand(BaseModel):
    """Команда обновления комнаты."""
    title: str | None = Field(None, min_length=1, max_length=100)
    max_users: int | None = Field(None, ge=1, le=1000)
    description: str | None = Field(None, max_length=500)
    avatar_url: str | None = None