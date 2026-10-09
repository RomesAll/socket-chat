from uuid import UUID
from sqlalchemy import select
from app.data_layer.repositories.base.base_repo import (
    BaseGetRepository,
    BaseSaveRepository,
    BaseDeleteRepository
)
from app.data_layer.models import MessageAttachment
from app.shared.dto.message import MessageAttachmentSaveDTO, MessageAttachmentGetDTO


class MessageRepository(
    BaseGetRepository[MessageAttachment],
    BaseSaveRepository[MessageAttachment, MessageAttachmentSaveDTO],
    BaseDeleteRepository[MessageAttachment]
):
    """Репозиторий для работы с медиафайлами сообщений"""

    MODEL: type[MessageAttachment] = MessageAttachment

    async def get_files_message(self, message_id: UUID) -> list[MessageAttachmentGetDTO]:
        """Получить список файлов сообщения."""
        stmt = (
            select(MessageAttachment)
            .where(
                MessageAttachment.message_id == message_id
            )
        )
        messages = (await self.session.scalars(stmt)).all()
        result = [MessageAttachmentGetDTO(**msg.to_dict()) for msg in messages]
        return result