from app.infrastructure.database.models import Message, MessageAttachment
from app.shared.dto.message import (
    MessageAttachmentGetDTO, MessageEncryptedReadDTO,
)


class MessageMapper:
    """Маппинг для агрегатов Message."""

    @staticmethod
    def to_read_dto(message_orm: Message) -> MessageEncryptedReadDTO:
        return MessageEncryptedReadDTO(
            id=message_orm.id,
            chat_id=message_orm.chat_id,
            sender_id=message_orm.sender_id,
            type=message_orm.type,
            reply_to_message_id=message_orm.reply_to_message_id,
            forwarded_from_message_id=message_orm.forwarded_from_message_id,
            forwarded_from_user_id=message_orm.forwarded_from_user_id,
            body_encrypted=message_orm.body_encrypted,
            is_edited=message_orm.is_edited,
            created_at=message_orm.created_at,
            updated_at=message_orm.updated_at,
        )

    @staticmethod
    def attachment_to_dto(attachment_orm: MessageAttachment) -> MessageAttachmentGetDTO:
        return MessageAttachmentGetDTO(
            id=attachment_orm.id,
            message_id=attachment_orm.message_id,
            file_name=attachment_orm.file_name,
            file_path=attachment_orm.file_path,
            mime_type=attachment_orm.mime_type,
            size=attachment_orm.size,
            created_at=attachment_orm.created_at,
            updated_at=attachment_orm.updated_at,
        )