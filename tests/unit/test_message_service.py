from unittest.mock import AsyncMock
from app.business_logic.services.message_service import MessageService
import pytest


@pytest.mark.asyncio
async def test_send_and_save_message(uow_mock, save_msg_dto, default_message_orm):
    """Тест для отправки и сохранения сообщения через mock"""
    uow_mock.msg_repo.save.return_value = default_message_orm

    cache = AsyncMock()
    broker = AsyncMock()

    msg_response = await MessageService(
        uow=uow_mock,
        cache=cache,
        broker=broker
    ).send_and_save_message(save_msg_dto)

    cache.save_chat_msg_info.assert_called_once()
    broker.publish_to_chat.assert_called_once()
    assert msg_response.id == save_msg_dto.id

