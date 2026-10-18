from datetime import datetime, timedelta, timezone
from uuid import UUID
import secrets
from app.business_logic.exceptions import (
    UrlTokenIsRevoked,
    UrlTokenMaxUses,
    UrlTokenNotFound
)
from app.infrastructure.mongo.invite_tokens.documents.invite_token import InviteTokenDoc
from app.infrastructure.mongo.invite_tokens.repositories.invite_token_repo import InviteTokenRepository
from app.shared.log_config import LogMixin


class InviteTokenService(LogMixin):
    """
    Операции с invite-токенами для вступления в комнаты.
    """

    def __init__(self, repo: InviteTokenRepository):
        self._repo = repo

    async def generate(
        self,
        room_id: UUID,
        created_by: str,
        hours: int,
        max_uses: int | None = None,
    ) -> str:
        """Генерация и сохранение urk токена."""

        token = secrets.token_urlsafe(32)
        expires_at = datetime.now(tz=timezone.utc) + timedelta(hours=hours)

        await self._repo.insert(InviteTokenDoc(
            token=token,
            room_id=str(room_id),
            created_by=created_by,
            expires_at=expires_at,
            max_uses=max_uses,
        ))

        self.log_info(f"Сгенерирован invite-токен для комнаты {room_id}")
        return token

    async def validate(self, token: str) -> InviteTokenDoc:
        """
        Проверить и использовать токен
        """
        doc = await self._repo.find_by_token(token)
        if not doc:
            raise UrlTokenNotFound(token)
        if doc.is_revoked:
            raise UrlTokenIsRevoked(token)
        if doc.expires_at < datetime.now(tz=timezone.utc):
            raise UrlTokenNotFound(token)
        if doc.max_uses is not None and doc.used_count >= doc.max_uses:
            raise UrlTokenMaxUses(token)

        await self._repo.increment_used(token)
        return doc

    async def revoke(self, token: str) -> None:
        """Отозвать токен."""
        await self._repo.revoke(token)
        self.log_info(f"Отозван invite-токен {token}")

    async def revoke_all_for_room(self, room_id: UUID) -> int:
        """Отозвать все токены комнаты."""
        count = await self._repo.revoke_all_for_room(room_id)
        self.log_info(f"Отозвано {count} invite-токенов комнаты {room_id}")
        return count