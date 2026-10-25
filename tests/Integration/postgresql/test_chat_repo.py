from uuid import uuid4
import pytest
from app.infrastructure.database.exceptions import IntegrityDBError
from app.infrastructure.database.models import Message
from app.infrastructure.database.repositories import ChatReadRepository, ChatRepository
from app.shared.dto.chat import ChatSaveDTO
from app.shared.dto.enums import ChatType, MessageType


async def test_create_chat_success(db_session):
    """Тест: Успешное сохранение нового чата"""
    chat_dto = ChatSaveDTO(id=uuid4(), type=ChatType.PRIVATE)
    repo = ChatRepository(db_session)
    new_chat = await repo.save(chat_dto)

    assert new_chat.id == chat_dto.id
    assert new_chat.type == chat_dto.type


async def test_create_chat_error(db_session, private_chat_setup):
    """Тест: Генерация исключения IntegrityDBError при попытках сохранить чат с сущ. id."""
    chat_id = private_chat_setup['chat'].id
    chat_dto = ChatSaveDTO(id=chat_id, type=ChatType.PRIVATE)
    repo = ChatRepository(db_session)

    with pytest.raises(IntegrityDBError):
        await repo.save(chat_dto)


async def test_get_user_chats(db_session, private_chat_setup):
    """
    Тест: Получить список чатов пользователя.
    """
    chat_id = private_chat_setup['chat'].id
    sender_id = private_chat_setup['members'][0].user_id
    msg = Message(
        id=uuid4(),
        chat_id=chat_id,
        sender_id=sender_id,
        body_encrypted=b'hello',
        type=MessageType.TEXT,
    )
    db_session.add(msg)
    await db_session.flush()

    chat_repo = ChatReadRepository(db_session)
    results = await chat_repo.get_user_chat_ids(sender_id)

    assert len(results) == 1
    assert results[0] == chat_id


async def test_user_is_member(db_session, private_chat_setup):
    """Тест: Переданный пользователь является участником чата"""
    chat_id = private_chat_setup['chat'].id
    member_id = private_chat_setup['members'][0].user_id

    chat_repo = ChatReadRepository(db_session)
    result = await chat_repo.is_member(chat_id, member_id)

    assert result is True