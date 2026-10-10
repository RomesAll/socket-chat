from uuid import uuid4
from app.data_layer.repositories import MessageRepository
from app.shared.dto.enums import MessageType
from app.shared.dto.message import MessageEncryptedSavedDTO


async def test_get_message_by_id_success(db_session, message_setup):
    """Тест: Получить сообщение по ID."""
    msg = message_setup['message']
    msg_repo = MessageRepository(db_session)
    result = await msg_repo.get_record_by_id(msg.id)

    assert result.id == msg.id


async def test_save_new_msg_success(db_session, private_chat_setup):
    """Тест: Успешное сохранение нового сообщения в чат."""
    chat_id = private_chat_setup['chat'].id
    sender_id = private_chat_setup['members'][0].user_id

    msg_dto = MessageEncryptedSavedDTO(
        id=uuid4(),
        chat_id=chat_id,
        sender_id=sender_id,
        type=MessageType.TEXT,
        body_encrypted='hello',
        reply_to_message_id=None,
        forwarded_from_message_id=None,
        forwarded_from_user_id=None
    )

    msg_repo = MessageRepository(db_session)
    result = await msg_repo.save(msg_dto)

    assert result.chat_id == chat_id
    assert result.sender_id == sender_id