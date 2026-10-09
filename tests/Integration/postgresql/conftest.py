from uuid import uuid4, UUID
import pytest
from app.data_layer.models import Chat, Room, User, ChatMember
from app.shared.dto.enums import ChatType, ChatRole, RoleEnum


@pytest.fixture(scope='function')
def chat_factory(db_session):
    """Фабрика для быстрого создания чатов в тестах."""
    async def _create_chat(chat_id: UUID, chat_type: ChatType) -> Chat:
        chat = Chat(
            id=chat_id,
            type=chat_type
        )
        db_session.add(chat)
        await db_session.flush()
        return chat
    return _create_chat


@pytest.fixture(scope='function')
def user_factory(db_session):
    """Фабрика для быстрого создания пользователей в тестах."""
    async def _create_user(
            user_id: str,
            display_name: str,
            role: RoleEnum,
            email: str,
            password: bytes
    ) -> User:
        user = User(
            id=user_id,
            display_name=display_name,
            role=role,
            email=email,
            password=password
        )
        db_session.add(user)
        await db_session.flush()
        return user
    return _create_user


@pytest.fixture(scope='function')
async def default_room_setup(
        db_session,
        user_factory,
        chat_factory
):
    """Фикстура для создания комнаты с чатом и пользователями."""
    chat = await chat_factory(chat_type=ChatType.ROOM, chat_id=uuid4())
    owner = await user_factory(
        user_id="room_owner",
        display_name="Owner",
        email="new@test.com",
        password=b"123",
        role=RoleEnum.DEFAULT_USER
    )

    member = ChatMember(chat_id=chat.id, user_id=owner.id, role=ChatRole.OWNER)
    db_session.add(member)

    room = Room(chat_id=chat.id, title='test')
    db_session.add(room)

    await db_session.flush()
    return {"chat": chat, "owner": owner, "room": room}


@pytest.fixture(scope='function')
async def private_chat_setup(
        db_session,
        user_factory,
        chat_factory
):
    """Фикстура для создания приватного чата с двумя пользователями."""
    chat = await chat_factory(chat_type=ChatType.PRIVATE, chat_id=uuid4())
    user_1 = await user_factory(
        user_id="room_owner",
        display_name="Owner",
        email="new@test.com",
        password=b"123",
        role=RoleEnum.DEFAULT_USER
    )
    user_2 = await user_factory(
        user_id="room_owner",
        display_name="Owner",
        email="new@test.com",
        password=b"123",
        role=RoleEnum.DEFAULT_USER
    )
    member_1 = ChatMember(chat_id=chat.id, user_id=user_1.id, role=ChatRole.MEMBER)
    member_2 = ChatMember(chat_id=chat.id, user_id=user_2.id, role=ChatRole.MEMBER)
    db_session.add_all([member_1, member_2])

    await db_session.flush()
    return {"chat": chat, "members": [member_1, member_2]}