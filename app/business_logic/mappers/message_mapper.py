from app.infrastructure.database.models import Message, MessageAttachment
from app.shared.dto.message import (
    MessageAttachmentGetDTO, MessageEncryptedReadDTO, MessageEncryptedGetDTO, ForwardedEncryptedMessageDTO,
    ReplyEncryptedMessageDTO,
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
    def to_read_dtos_with_rel(orm_messages: list[Message]) -> list[MessageEncryptedGetDTO]:
        dto_messages = []
        for orm in orm_messages:
            reply_to, forwarded_from = None, None
            if orm.reply_to:
                reply_to = ReplyEncryptedMessageDTO(
                    id=orm.reply_to.id,
                    type=orm.reply_to.type,
                    body_encrypted=orm.reply_to.body_encrypted
                )
            if orm.forwarded_from:
                forwarded_from = ForwardedEncryptedMessageDTO(
                    forwarded_from_message_id=orm.forwarded_from.id,
                    type=orm.forwarded_from.type,
                    body_encrypted=orm.forwarded_from.body_encrypted,
                    forwarded_from_user_id=orm.forwarded_from.forwarded_from_user_id
                )
            dto_messages.append(MessageEncryptedGetDTO(
                id=orm.id,
                chat_id=orm.chat_id,
                sender_id=orm.sender_id,
                type=orm.type,
                body_encrypted=orm.body_encrypted,
                is_edited=orm.is_edited,
                created_at=orm.created_at,
                updated_at=orm.updated_at,
                reply_to=reply_to,
                forwarded_from=forwarded_from
            ))
        return dto_messages

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