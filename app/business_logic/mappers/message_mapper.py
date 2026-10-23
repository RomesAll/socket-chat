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
    def to_read_dtos_with_rel(orm_message: Message) -> MessageEncryptedGetDTO:
        reply_to, forwarded_from, files = None, None, []

        if orm_message.reply_to:
            reply_to = ReplyEncryptedMessageDTO(
                id=orm_message.reply_to.id,
                type=orm_message.reply_to.type,
                body_encrypted=orm_message.reply_to.body_encrypted
            )

        if orm_message.forwarded_from:
            fwd_files = []
            # Подгружаем файлы из оригинала
            fwd_orm_files = getattr(orm_message.forwarded_from, 'files', [])
            if fwd_orm_files:
                for file in fwd_orm_files:
                    fwd_files.append(MessageAttachmentGetDTO(
                        id=file.id,
                        message_id=file.message_id,
                        file_name=file.file_name,
                        file_path=file.file_path,
                        mime_type=file.mime_type,
                        size=file.size,
                        created_at=file.created_at,
                        updated_at=file.updated_at
                    ))

            forwarded_from = ForwardedEncryptedMessageDTO(
                forwarded_from_message_id=orm_message.forwarded_from.id,
                type=orm_message.forwarded_from.type,
                body_encrypted=orm_message.forwarded_from.body_encrypted,
                forwarded_from_user_id=orm_message.forwarded_from_user_id,
                files=fwd_files,
                chat_id=orm_message.forwarded_from.chat_id
            )

        if orm_message.files:
            for file in orm_message.files:
                files.append(MessageAttachmentGetDTO(
                    id=file.id,
                    message_id=file.message_id,
                    file_name=file.file_name,
                    file_path=file.file_path,
                    mime_type=file.mime_type,
                    size=file.size,
                    created_at=file.created_at,
                    updated_at=file.updated_at
                ))

        return MessageEncryptedGetDTO(
            id=orm_message.id,
            chat_id=orm_message.chat_id,
            sender_id=orm_message.sender_id,
            type=orm_message.type,
            body_encrypted=orm_message.body_encrypted,
            is_edited=orm_message.is_edited,
            created_at=orm_message.created_at,
            updated_at=orm_message.updated_at,
            reply_to=reply_to,
            forwarded_from=forwarded_from,
            files=files
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