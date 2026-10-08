from datetime import datetime
from uuid import UUID

from mongotic import MongoBaseModel, mapped_field, Mapped
from motor.motor_asyncio import AsyncIOMotorClient


async def ensure_invite_ttl_index(client: AsyncIOMotorClient):
    """
    Создание индекса для автоматического удаление документа,
    после истечение время жизни
    """
    collection = client["messenger_db"]["invite_url_tokens"]
    await collection.create_index(
        [("expires_at", 1)],
        name="expires_at_ttl",
        expireAfterSeconds=0,
    )


class InviteUrl(MongoBaseModel):
    """Модель для хранения информации о url токене"""
    __databasename__ = "messenger_db"
    __tablename__ = "invite_url_tokens"

    token: Mapped[str]
    actor_id: Mapped[str]
    room_id: Mapped[UUID]
    created_at: Mapped[datetime]
    expires_at: Mapped[datetime]
    max_uses: Mapped[int | None] = mapped_field(default=None)
    uses_count: Mapped[int]
    is_revoked: Mapped[bool] = mapped_field(default=False)
