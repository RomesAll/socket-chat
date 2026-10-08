from uuid import UUID
from app.data_layer.repositories.base.base_repo import (
    BaseGetRepository,
    BaseSaveRepository,
    BaseUpdateRepository,
    BaseDeleteRepository
)
from app.shared.dto.room import RoomSaveDTO, RoomUpdateDTO
from app.data_layer.models import Room


class RoomRepository(
    BaseGetRepository[Room],
    BaseSaveRepository[Room, RoomSaveDTO],
    BaseUpdateRepository[Room, RoomUpdateDTO],
    BaseDeleteRepository[Room]
):
    """
    Репозиторий для записи и точечного чтения комнат (write-side).

    Отвечает за создание, обновление и удаление ORM-модели Room,
    а также за получение отдельной комнаты по идентификатору
    для сценариев записи.
    """

    MODEL: type[Room] = Room

    async def set_owner(self, room_id: UUID, new_owner: str) -> Room:
        """
        Поменять поле `owner_id` для комнаты в базе данных.

        :param room_id: Идентификатор комнаты.
        :param new_owner: ID нового владельца.
        :return: Обновленная ORM-модель Room в сессии.
        """
        room_info = await self.get_record_by_id(room_id)
        room_info.owner_id = new_owner
        await self.session.flush()
        return room_info

    async def find_by_id(self, room_id: UUID) -> Room | None:
        """
        Получить ORM-модель Room или None.

        В отличие от `get_record_by_id`, не кидает исключение,
        если комната не найдена — используется в сценариях,
        где отсутствие записи допустимо.

        :param room_id: Идентификатор комнаты.
        :return: Объект ORM модели Room или None, если комнаты нет.
        """
        return await self.session.get(self.MODEL, room_id)

    async def get_owner_room(self, room_id: UUID) -> str | None:
        """
        Получить идентификатор владельца комнаты или None.

        Возвращает None, если комната существует, но владелец не задан.
        Кидает RecordNotFound, если комнаты с таким id нет.

        :param room_id: Идентификатор комнаты.
        :return: ID владельца или None, если владелец не задан.
        :raises RecordNotFound: Если комнаты с таким id не существует.
        """
        room_info = await self.get_record_by_id(room_id)
        return room_info.owner_id