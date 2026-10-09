from uuid import uuid4
import pytest
from app.data_layer.models import Room, User, RoomMember, Chat
from app.data_layer.repositories.room.read import RoomReadRepository
from app.data_layer.repositories.room.write import RoomRepository
from app.data_layer.exceptions import RecordNotFound
from app.shared.dto.room import RoomSaveDTO, RoomUpdateDTO
from app.shared.dto.enums import RoomRole


async def test_save_room_success(db_session, add_private_chat):
    """Тест: Успешное добавление новой комнаты в сессии БД."""
    save_dto = RoomSaveDTO(chat_id=add_private_chat.id, name='Тестовая комната')
    room_repo = RoomRepository(db_session)
    result = await room_repo.save(save_dto)
    await db_session.commit()

    assert result.chat_id == save_dto.chat_id
    assert result.owner_id is None
    assert result.name == save_dto.name


async def test_update_room_success(db_session, add_private_chat, add_room):
    """Тест: Успешное обновление комнаты в сессии БД."""
    room_repo = RoomRepository(db_session)
    update_dto = RoomUpdateDTO(name='Обновленная комната')
    updated_room = await room_repo.update(add_room.chat_id, update_dto)

    await db_session.commit()
    assert updated_room.name == update_dto.name


async def test_change_owner_success(db_session, add_private_chat, add_room):
    """Тест: Успешное изменение ID владельца комнаты в сессии БД."""
    # Создание пользователей в БД, чтобы не ломать ForeignKey
    old_owner_id = "user_old_id"
    new_owner_id = "user_new_id"

    # Создание старого и нового владельца
    old_user = User(id=old_owner_id, display_name="Old Owner", email="old@test.com", password=b"123")
    new_user = User(id=new_owner_id, display_name="New Owner", email="new@test.com", password=b"123")

    db_session.add_all([old_user, new_user])
    await db_session.commit()

    repo = RoomRepository(session=db_session)
    updated_room = await repo.set_owner(room_id=add_room.chat_id, new_owner=new_owner_id)

    assert updated_room.owner_id == new_owner_id

    refreshed_room = await db_session.get(Room, add_room.chat_id)
    assert refreshed_room.owner_id == new_owner_id


async def test_change_owner_room_not_found(db_session):
    """
    Тест: Получение исключения RecordNotFound при смене
    владельца в несуществующей комнате.
    """
    repo = RoomRepository(db_session)
    with pytest.raises(RecordNotFound):
        await repo.set_owner(uuid4(), 'user_new_id')


async def test_find_by_id_returns_room_when_exists(db_session, add_private_chat):
    """Тест: Успешное получение ORM-модели Room из сессии БД."""
    new_room = RoomSaveDTO(chat_id=add_private_chat.id, name='Тестовая комната')
    repo = RoomRepository(db_session)
    created = await repo.save(new_room)
    await db_session.commit()

    result = await repo.find_by_id(room_id=created.chat_id)

    assert result is not None
    assert result.chat_id == created.chat_id
    assert result.name == 'Тестовая комната'


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
    new_chat = Chat(id=uuid4(), type='private')
    db_session.add(new_chat)
    await db_session.commit()

    user_id = 'new_user'
    new_user = User(id=user_id, display_name="New Owner", email="new@test.com", password=b"123")
    db_session.add(new_user)
    await db_session.commit()

    test_room = Room(chat_id=new_chat.id, name="Тестовая комната", owner_id=user_id)
    db_session.add(test_room)
    await db_session.commit()

    repo = RoomRepository(db_session)
    result = await repo.get_owner_room(room_id=new_chat.id)
    assert result == user_id


async def test_get_owner_by_id_room_not_found(db_session):
    """
    Тест: Генерация исключения RecordNotFound при получении
    владельца несуществующей комнаты
    """
    repo = RoomRepository(db_session)
    with pytest.raises(RecordNotFound):
        await repo.get_owner_room(room_id=uuid4())


async def test_get_user_rooms_when_exists(db_session):
    """Тест: Получение комнат пользователя, роли в комнатах и кол-во участников"""
    new_chat = Chat(id=uuid4(), type='private')
    db_session.add(new_chat)
    await db_session.commit()

    new_user_1 = User(id='new_user_1', display_name="New user 1", email="new1@test.com", password=b"123")
    new_user_2 = User(id='new_user_2', display_name="New user 2", email="new2@test.com", password=b"123")
    db_session.add_all([new_user_1, new_user_2])
    await db_session.flush()

    test_room = Room(chat_id=new_chat.id, name="Тестовая комната", owner_id=new_user_1.id)
    db_session.add(test_room)
    await db_session.flush()

    room_member_1 = RoomMember(
        room_id=new_chat.id,
        user_id=new_user_1.id,
        role=RoomRole.OWNER,
        is_access_private_chat=True
    )
    room_member_2 = RoomMember(
        room_id=new_chat.id,
        user_id=new_user_2.id,
        role=RoomRole.MEMBER
    )
    db_session.add_all([room_member_1, room_member_2])
    await db_session.flush()

    room_read_repo = RoomReadRepository(db_session)
    user_rooms = await room_read_repo.get_user_rooms(user_id=new_user_1.id)
    assert len(user_rooms) == 1
    assert user_rooms[0].owner_id == new_user_1.id
    assert user_rooms[0].members_count == 2
    assert user_rooms[0].role == RoomRole.OWNER