from dataclasses import asdict
from datetime import datetime, timezone, timedelta
import secrets
from mongotic import select
from mongotic.asyncio import AsyncSession
from app.business_logic.exceptions import UrlTokenNotFound, UrlTokenMaxUses, UrlTokenIsRevoked
from app.data_layer.models.invite_url import InviteUrl
from app.shared.dto.room import GenerateInviteToken


class InviteUrlRepo:
    """Репозиторий для работы с url токенами для приглашения в чаты, комнаты"""
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save_url_token(self, url_info: GenerateInviteToken) -> tuple[str, datetime]:
        """Генерация и сохранения url ссылки"""
        token = secrets.token_urlsafe(32)
        exp = datetime.now(tz=timezone.utc) + timedelta(hours=url_info.hours)
        orm_model = InviteUrl(
            token=token,
            expires_at=exp,
            uses_count=0,
            created_at=datetime.now(tz=timezone.utc),
            **asdict(url_info)
        )
        self.session.add(orm_model)
        await self.session.flush()
        return token, exp

    async def get_url_token(self, token: str) -> InviteUrl:
        """Получить документ url токена из БД."""
        document = await self.session.scalar(
            select(InviteUrl)
            .where(InviteUrl.token == token)
        )
        if not document:
            raise UrlTokenNotFound(token)
        if document and document.is_revoked:
            raise UrlTokenIsRevoked(token)
        return document

    async def increment_count_uses(self, document: InviteUrl) -> int:
        """Применить ulr токен"""
        if document.uses_count == document.max_uses:
            raise UrlTokenMaxUses(document.token)
        document.uses_count += 1
        await self.session.flush()
        return document.uses_count