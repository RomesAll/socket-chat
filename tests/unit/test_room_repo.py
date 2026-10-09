from uuid import uuid4
from app.data_layer.models import Room, User, Chat, ChatMember
from app.data_layer.repositories.room.read import RoomReadRepository
from app.data_layer.repositories.room.write import RoomRepository
from app.shared.dto.room import RoomSaveDTO, RoomUpdateDTO
from app.shared.dto.enums import ChatRole, ChatType


async def test_save_room_success(db_session):
    """Тест: Успешное добавление новой комнаты в сессии БД."""
    new_chat = Chat(id=uuid4(), type=ChatType.ROOM)
    db_session.add(new_chat)
    await db_session.commit()

    save_dto = RoomSaveDTO(chat_id=new_chat.id, title='Тестовая комната')
    room_repo = RoomRepository(db_session)
    result = await room_repo.save(save_dto)
    await db_session.commit()

    assert result.chat_id == save_dto.chat_id
    assert result.title == save_dto.title


async def test_update_room_success(db_session, add_room):
    """Тест: Успешное обновление комнаты в сессии БД."""
    room_repo = RoomRepository(db_session)
    update_dto = RoomUpdateDTO(title='Обновленная комната')
    updated_room = await room_repo.update(add_room.chat_id, update_dto)

    await db_session.commit()
    assert updated_room.title == update_dto.title


async def test_find_by_id_returns_room_when_exists(db_session, add_private_chat):
    """Тест: Успешное получение ORM-модели Room из сессии БД."""
    new_room = RoomSaveDTO(chat_id=add_private_chat.id, title='Тестовая комната')
    repo = RoomRepository(db_session)
    created = await repo.save(new_room)
    await db_session.commit()

    result = await repo.find_by_id(room_id=created.chat_id)

    assert result is not None
    assert result.chat_id == created.chat_id
    assert result.title == 'Тестовая комната'


async def test_find_by_id_returns_none(db_session):
    """
    Тест: Получение None вместо ORM-модели Room,
    т.к. комнаты не была добавлена ранее в сессию БД.
    """
    repo = RoomRepository(db_session)
    result = await repo.find_by_id(room_id=uuid4())
    assert result is None


async def test_get_owner_by_id_room_returns_when_exists(db_session):
    """Тест: Получения ID владельца комнаты."""
    new_chat = Chat(id=uuid4(), type=ChatType.ROOM)
    db_session.add(new_chat)
    await db_session.commit()

    user_id = 'new_user'
    new_user = User(id=user_id, display_name="New Owner", email="new@test.com", password=b"123")
    db_session.add(new_user)
    await db_session.commit()

    test_room = Room(chat_id=new_chat.id, title="Тестовая комната")
    db_session.add(test_room)
    await db_session.commit()

    chat_member_1 = ChatMember(chat_id=new_chat.id, user_id=new_user.id, role=ChatRole.OWNER)
    db_session.add_all([chat_member_1])
    await db_session.commit()

    repo = RoomReadRepository(db_session)
    result = await repo.get_owner_room(room_id=new_chat.id)
    assert result == user_id


async def test_get_owner_by_id_room_not_found(db_session):
    """
    Тест: Неудачная попытка поиска владельца комнаты
    владельца несуществующей комнаты.
    """
    repo = RoomReadRepository(db_session)
    result = await repo.get_owner_room(room_id=uuid4())
    assert result is None


async def test_user_is_room_member(db_session):
    """Тест: Переданный пользователь является участником комнаты."""
    new_chat = Chat(id=uuid4(), type=ChatType.ROOM)
    db_session.add(new_chat)
    await db_session.commit()

    new_user_1 = User(id='new_user_1', display_name="New user 1", email="new1@test.com", password=b"123")
    db_session.add_all([new_user_1])
    await db_session.commit()

    chat_member_1 = ChatMember(chat_id=new_chat.id, user_id=new_user_1.id, role=ChatRole.OWNER)
    db_session.add_all([chat_member_1])
    await db_session.commit()

    test_room = Room(chat_id=new_chat.id, title="Тестовая комната")
    db_session.add(test_room)
    await db_session.commit()

    repo = RoomReadRepository(db_session)
    result = await repo.is_member(test_room.chat_id, new_user_1.id)

    assert result == True


async def test_get_user_rooms_when_exists(db_session):
    """Тест: Получение комнат пользователя, роли в комнатах и кол-во участников."""
    new_chat = Chat(id=uuid4(), type=ChatType.PRIVATE)
    db_session.add(new_chat)
    await db_session.commit()

    new_user_1 = User(id='new_user_1', display_name="New user 1", email="new1@test.com", password=b"123")
    new_user_2 = User(id='new_user_2', display_name="New user 2", email="new2@test.com", password=b"123")
    new_user_3 = User(id='new_user_3', display_name="New user 3", email="new3@test.com", password=b"123")
    db_session.add_all([new_user_1, new_user_2, new_user_3])
    await db_session.commit()

    chat_member_1 = ChatMember(chat_id=new_chat.id, user_id=new_user_1.id, role=ChatRole.OWNER)
    chat_member_2 = ChatMember(chat_id=new_chat.id, user_id=new_user_2.id, role=ChatRole.MEMBER)
    chat_member_3 = ChatMember(chat_id=new_chat.id, user_id=new_user_3.id, role=ChatRole.MEMBER)
    db_session.add_all([chat_member_1, chat_member_2, chat_member_3])
    await db_session.commit()

    test_room = Room(chat_id=new_chat.id, title="Тестовая комната")
    db_session.add(test_room)
    await db_session.commit()

    room_read_repo = RoomReadRepository(db_session)
    user_rooms = await room_read_repo.get_user_rooms(user_id=new_user_1.id)

    assert len(user_rooms) == 1
    assert user_rooms[0].members_count == 3
    assert user_rooms[0].chat_id == new_chat.id
    assert user_rooms[0].role == ChatRole.OWNER