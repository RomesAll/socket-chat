from uuid import uuid4
import pytest
from app.data_layer.models import Room, User
from app.data_layer.repositories.room.write import RoomRepository
from app.data_layer.exceptions import RecordNotFound
from app.shared.dto import RoomDtoSave


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
    updated_room = await repo.change_owner(room_id=room_id, new_owner=new_owner_id)

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
        await repo.change_owner(uuid4(), 'user_new_id')


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
    user_id = uuid4()
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