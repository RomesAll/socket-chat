from uuid import UUID
from app.infrastructure.database.repositories.base.base_repo import (
    BaseGetRepository,
    BaseSaveRepository,
    BaseUpdateRepository,
    BaseDeleteRepository
)
from app.shared.dto.room import RoomSaveDTO, RoomUpdateDTO
from app.infrastructure.database.models import Room


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