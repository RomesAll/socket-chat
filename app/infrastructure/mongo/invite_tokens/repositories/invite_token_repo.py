from dataclasses import asdict
from datetime import datetime
from uuid import UUID
from ..documents.invite_token import InviteTokenDoc


class InviteTokenRepository:
    """Репозиторий токенов для вступления."""

    def __init__(self, db):
        self._collection = db["invite_tokens"]

    async def insert(self, doc: InviteTokenDoc) -> None:
        await self._collection.insert_one(asdict(doc))

    async def find_by_token(self, token: str) -> InviteTokenDoc | None:
        raw = await self._collection.find_one({"token": token})
        if not raw:
            return None
        return InviteTokenDoc(
            token=raw["token"],
            room_id=raw["room_id"],
            created_by=raw["created_by"],
            expires_at=raw["expires_at"],
            max_uses=raw.get("max_uses"),
            used_count=raw.get("used_count", 0),
            is_revoked=raw.get("is_revoked", False),
            created_at=raw["created_at"],
        )

    async def increment_used(self, token: str) -> None:
        await self._collection.update_one(
            {"token": token},
            {"$inc": {"used_count": 1}},
        )

    async def revoke(self, token: str) -> None:
        await self._collection.update_one(
            {"token": token},
            {"$set": {"is_revoked": True}},
        )

    async def revoke_all_for_room(self, room_id: UUID) -> int:
        result = await self._collection.update_many(
            {"room_id": str(room_id), "is_revoked": False},
            {"$set": {"is_revoked": True}},
        )
        return result.modified_count

    async def delete_expired(self) -> int:
        result = await self._collection.delete_many({
            "expires_at": {"$lt": datetime.utcnow()},
        })
        return result.deleted_count