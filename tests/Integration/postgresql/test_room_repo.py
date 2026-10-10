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
    await db_session.flush()

    save_dto = RoomSaveDTO(chat_id=new_chat.id, title='Тестовая комната')
    room_repo = RoomRepository(db_session)

    result = await room_repo.save(save_dto)
    await db_session.flush()

    assert result.chat_id == save_dto.chat_id
    assert result.title == save_dto.title


async def test_update_room_success(db_session, default_room_setup):
    """Тест: Успешное обновление комнаты в сессии БД."""
    room_repo = RoomRepository(db_session)
    update_dto = RoomUpdateDTO(title='Обновленная комната')
    updated_room = await room_repo.update(default_room_setup['room'].chat_id, update_dto)

    await db_session.flush()
    assert updated_room.title == update_dto.title


async def test_find_by_id_returns_room_when_exists(db_session, default_room_setup):
    """Тест: Успешное получение ORM-модели Room из сессии БД."""
    room_id = default_room_setup['room'].chat_id
    repo = RoomRepository(db_session)
    result = await repo.find_by_id(room_id=room_id)

    assert result is not None
    assert result.chat_id == room_id
    assert result.title == 'test'


async def test_find_by_id_returns_none(db_session):
    """
    Тест: Получение None вместо ORM-модели Room,
    т.к. комнаты не была добавлена ранее в сессию БД.
    """
    repo = RoomRepository(db_session)
    result = await repo.find_by_id(room_id=uuid4())
    assert result is None


async def test_get_owner_by_id_room_returns_when_exists(db_session, default_room_setup):
    """Тест: Получения ID владельца комнаты."""
    owner = default_room_setup['owner']
    room_id= default_room_setup['room'].chat_id
    repo = RoomReadRepository(db_session)
    result = await repo.get_owner_room(room_id=room_id)
    assert result == owner.user_id


async def test_get_owner_by_id_room_not_found(db_session):
    """
    Тест: Неудачная попытка поиска владельца комнаты
    владельца несуществующей комнаты.
    """
    repo = RoomReadRepository(db_session)
    result = await repo.get_owner_room(room_id=uuid4())
    assert result is None


async def test_user_is_room_member(db_session, default_room_setup):
    """Тест: Переданный пользователь является участником комнаты."""
    repo = RoomReadRepository(db_session)
    result = await repo.is_member(
        default_room_setup['room'].chat_id, default_room_setup['owner'].user_id
    )
    assert result == True


async def test_get_user_rooms_when_exists(db_session, default_room_setup):
    """Тест: Получение комнат пользователя, роли в комнатах и кол-во участников."""
    user_id = default_room_setup['owner'].user_id
    chat = default_room_setup['chat']
    room_read_repo = RoomReadRepository(db_session)
    user_rooms = await room_read_repo.get_user_rooms(user_id=user_id)

    assert len(user_rooms) == 1
    assert user_rooms[0].members_count == 1
    assert user_rooms[0].chat_id == chat.id
    assert user_rooms[0].role == ChatRole.OWNER