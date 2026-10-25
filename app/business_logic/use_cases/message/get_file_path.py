from pathlib import Path
from uuid import UUID
from app.business_logic.exceptions import UserIsNotMember
from app.business_logic.services import MessageService, ChatService
from app.shared.dto.message import MessageAttachmentGetDTO


class GetFilePathUseCase:
    """
    Получить путь к файлу для скачивания.

    Сценарий:
    - Получить информацию о файле и проверить существования.
    - Проверить, является ли пользователь участником чата.
    - Получить путь к файлу для скачивания.
    """

    def __init__(
        self,
        chat_service: ChatService,
        message_service: MessageService,
    ):
        self._chat_service = chat_service
        self._message_service = message_service

    async def execute(self, file_id: UUID, user_id: str, chat_id) -> MessageAttachmentGetDTO:
        if not await self._chat_service.is_member(chat_id, user_id):
            raise UserIsNotMember(user_id, chat_id)

        file_info = await self._message_service.get_attachment(file_id)
        path = Path(file_info.file_path)
        if not path.exists():
            raise FileNotFoundError()

        return file_info