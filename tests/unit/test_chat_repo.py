from uuid import uuid4
from app.data_layer.models import Message, Chat, User, ChatMember
from app.data_layer.repositories.chat import ChatReadRepository
from app.shared.dto import MessageType
from app.shared.dto.enums import ChatType, ChatRole


async def test_get_user_chats(db_session):
    """
    Тест: Получить список чатов пользователя, отсортированных по дате
    последнего сообщения.
    """
    user = User(
        id='user_id',
        display_name="New Owner",
        email="new@test.com",
        password=b"123"
    )
    db_session.add(user)
    await db_session.commit()

    chat = Chat(
        id=uuid4(),
        type=ChatType.PRIVATE
    )
    db_session.add(chat)
    await db_session.commit()

    chat_member = ChatMember(
        chat_id=chat.id,
        user_id=user.id,
        role=ChatRole.MEMBER,
    )
    db_session.add(chat_member)
    await db_session.commit()

    msg = Message(
        id=uuid4(),
        chat_id=chat.id,
        sender_id=user.id,
        body_encrypted='hello',
        type=MessageType.TEXT,
    )
    db_session.add(msg)
    await db_session.commit()

    chat_repo = ChatReadRepository(db_session)
    results = await chat_repo.get_user_chats(user.id)

    assert results[0].id == chat.id
    assert results[0].is_active == True


async def test_user_is_member(db_session):
    """Тест: Переданный пользователь является участником чата"""
    user = User(
        id='user_id',
        display_name="New Owner",
        email="new@test.com",
        password=b"123"
    )
    db_session.add(user)
    await db_session.commit()

    chat = Chat(
        id=uuid4(),
        type=ChatType.PRIVATE
    )
    db_session.add(chat)
    await db_session.commit()

    chat_member = ChatMember(
        chat_id=chat.id,
        user_id=user.id,
        role=ChatRole.MEMBER,
    )
    db_session.add(chat_member)
    await db_session.commit()

    chat_repo = ChatReadRepository(db_session)
    result = await chat_repo.is_member(chat.id, user.id)

    assert result is True