from uuid import uuid4
import pytest
from app.business_logic.exceptions import UrlTokenMaxUses
from app.data_layer.repositories.invite_url_repo import InviteUrlRepo
from app.shared.dto.room import GenerateInviteToken
from datetime import datetime, timezone, timedelta


async def test_save_url_token_success(db_mongo_session):
    """Тест: Успешная генерация url токена для вступления в комнату"""
    toke_dto = GenerateInviteToken(
        actor_id='user_id',
        room_id=uuid4(),
        hours=4,
        max_uses=3,
    )
    repo = InviteUrlRepo(db_mongo_session)
    token, exp = await repo.save_url_token(toke_dto)
    assert len(token) == 43
    assert exp <= datetime.now(tz=timezone.utc) + timedelta(toke_dto.hours)


async def test_get_url_toke_success(db_mongo_session):
    """Тест: Успешное получение url токена из БД."""
    toke_dto = GenerateInviteToken(
        actor_id='user_id',
        room_id=uuid4(),
        hours=4,
        max_uses=3,
    )
    repo = InviteUrlRepo(db_mongo_session)
    token, exp = await repo.save_url_token(toke_dto)
    token_info = await repo.get_url_token(token)

    assert token_info.token == token
    assert token_info.max_uses == toke_dto.max_uses
    assert token_info.actor_id == toke_dto.actor_id


async def test_increment_use_count_url(db_mongo_session):
    """Тест: Уличение счетчика использования токена."""
    toke_dto = GenerateInviteToken(
        actor_id='user_id',
        room_id=uuid4(),
        hours=4,
        max_uses=3,
    )
    repo = InviteUrlRepo(db_mongo_session)
    token, exp = await repo.save_url_token(toke_dto)
    token_info = await repo.get_url_token(token)
    new_count = await repo.increment_count_uses(token_info)

    assert token_info.token == token
    assert new_count == 1


async def test_increment_use_count_max_uses(db_mongo_session):
    """Тест: Генерация UrlTokenMaxUses при максимальном кол-ве использований."""
    toke_dto = GenerateInviteToken(
        actor_id='user_id',
        room_id=uuid4(),
        hours=4,
        max_uses=3,
    )
    repo = InviteUrlRepo(db_mongo_session)
    token, exp = await repo.save_url_token(toke_dto)
    token_info = await repo.get_url_token(token)
    with pytest.raises(UrlTokenMaxUses):
        for _ in range(4):
            await repo.increment_count_uses(token_info)