from uuid import uuid4
import pytest
from app.data_layer.models import Room, User, RoomMember
from app.data_layer.repositories.room.read import RoomReadRepository
from app.data_layer.repositories.room.write import RoomRepository
from app.data_layer.exceptions import RecordNotFound
from app.shared.dto import RoomDtoSave
from app.shared.dto.enums import RoomRole


async def test_change_owner_success(db_session):
    """Тест: Успешное изменение ID владельца комнаты в сессии БД."""

    # Создание пользователей в БД, чтобы не ломать ForeignKey
    old_owner_id = "user_old_id"
    new_owner_id = "user_new_id"

    # Создание старого и нового владельца
    old_user = User(id=old_owner_id, display_name="Old Owner", email="old@test.com", password=b"123")
    new_user = User(id=new_owner_id, display_name="New Owner", email="new@test.com", password=b"123")

    db_session.add_all([old_user, new_user])
    await db_session.flush()

    # Создание комнаты с реальным owner_id
    room_id = uuid4()
    test_room = Room(id=room_id, name="Тестовая комната", owner_id=old_owner_id)

    db_session.add(test_room)
    await db_session.commit()

    repo = RoomRepository(session=db_session)
    updated_room = await repo.set_owner(room_id=room_id, new_owner=new_owner_id)

    assert updated_room.owner_id == new_owner_id

    refreshed_room = await db_session.get(Room, room_id)
    assert refreshed_room.owner_id == new_owner_id


async def test_change_owner_room_not_found(db_session):
    """
    Тест: Получение исключения RecordNotFound при смене
    владельца в несуществующей комнате.
    """
    repo = RoomRepository(db_session)
    with pytest.raises(RecordNotFound):
        await repo.set_owner(uuid4(), 'user_new_id')


async def test_find_by_id_returns_room_when_exists(db_session):
    """Тест: Успешное получение ORM-модели Room из сессии БД."""
    new_room = RoomDtoSave(id=uuid4(), name='Тестовая комната')
    repo = RoomRepository(db_session)
    created = await repo.save(new_room)
    await db_session.commit()

    result = await repo.find_by_id(room_id=created.id)

    assert result is not None
    assert result.id == created.id
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
    user_id = 'new_user'
    new_user = User(id=user_id, display_name="New Owner", email="new@test.com", password=b"123")
    db_session.add(new_user)
    await db_session.commit()

    room_id = uuid4()
    test_room = Room(id=room_id, name="Тестовая комната", owner_id=user_id)
    db_session.add(test_room)
    await db_session.commit()

    repo = RoomRepository(db_session)
    result = await repo.get_owner_room(room_id=room_id)
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
    new_user_1 = User(id='new_user_1', display_name="New user 1", email="new1@test.com", password=b"123")
    new_user_2 = User(id='new_user_2', display_name="New user 2", email="new2@test.com", password=b"123")
    db_session.add_all([new_user_1, new_user_2])
    await db_session.flush()

    test_room = Room(id=uuid4(), name="Тестовая комната", owner_id=new_user_1.id)
    db_session.add(test_room)
    await db_session.flush()

    room_member_1 = RoomMember(
        room_id=test_room.id,
        user_id=new_user_1.id,
        role=RoomRole.OWNER,
        is_access_private_chat=True
    )
    room_member_2 = RoomMember(
        room_id=test_room.id,
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