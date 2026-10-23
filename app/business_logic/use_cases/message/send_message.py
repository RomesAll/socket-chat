from datetime import datetime, timezone
from uuid import uuid4
from fastapi import UploadFile
from app.business_logic.exceptions import PermissionError, TargetSendNotFound, ReplyMessageForwardedError
from app.business_logic.services import MessageService, ChatService
from app.business_logic.unit_of_work import UnitOfWork
from app.domain.events.audit import AuditEvent, Context
from app.domain.events.enums import ActionType
from app.infrastructure.redis import UnreadCache
from app.infrastructure.security import SymmetricEncode
from app.infrastructure.storage.file_manager import AsyncFileAdapter
from app.infrastructure.websocket import WSBroker
from app.shared.config import BaseConfig
from app.shared.dto.audit import RequestMeta
from app.shared.dto.chat import ChatDTO, ChatSaveDTO, ChatMemberSaveDTO, ChatUpdateDTO
from app.shared.dto.enums import ChatType, ChatRole
from app.shared.dto.message import (
    SendMessage,
    MessageEncryptedSavedDTO,
    MessageAttachmentSaveDTO,
    ReplyMessageDTO,
    ForwardedMessageDTO,
    MessageGetDTO,
    MessageEncryptedGetDTO
)
from app.shared.log_config import LogMixin


class SendMessageUseCase(LogMixin):
    """Отправить сообщение"""

    def __init__(
            self,
            message_service: MessageService,
            chat_service: ChatService,
            ws_broker: WSBroker,
            unread_cache: UnreadCache,
            uow: UnitOfWork,
            file_storage: AsyncFileAdapter,
            encoder: SymmetricEncode,
            config: BaseConfig
    ):
        self._message_service = message_service
        self._chat_service = chat_service
        self._ws_broker = ws_broker
        self._unread_cache = unread_cache
        self._uow = uow
        self._file_storage = file_storage
        self._encoder = encoder
        self._config = config

    async def execute(
            self,
            msg: SendMessage,
            files: list[UploadFile],
            actor_id: str,
            request_meta: RequestMeta
    ) -> MessageGetDTO:

        if not msg.chat_id and not msg.recipient_id:
            raise TargetSendNotFound()

        if all([msg.reply_to_message_id, msg.forwarded_from_user_id, msg.forwarded_from_message_id]):
            raise ReplyMessageForwardedError()

        # Получить или создать (приватный) чат
        is_new_chat = False
        if msg.chat_id:
            chat = await self._chat_service.get(msg.chat_id)
        else:
            if not msg.recipient_id:
                raise TargetSendNotFound()

            # Проверяем, существует ли уже чат
            existing_chat = await self._chat_service.find_between_users(actor_id, msg.recipient_id)
            if existing_chat:
                chat = existing_chat
            else:
                chat = await self._get_or_create_private_chat(actor_id, msg.recipient_id)
                is_new_chat = True

        # Проверить права
        is_member = await self._chat_service.get_member(chat.id, actor_id)
        if not is_member:
            self.log_warning(f"Пользователь {actor_id} не участник чата {chat.id}")
            raise PermissionError(f"Пользователь {actor_id} не участник чата {chat.id}")

        # Сохранить сообщение
        body_encrypted = self._encoder.encrypt(msg.text) if msg.text else None
        encrypt_msg_dto = MessageEncryptedSavedDTO(
            id=uuid4(),
            chat_id=chat.id,
            sender_id=actor_id,
            type=msg.type,
            reply_to_message_id=msg.reply_to_message_id,
            forwarded_from_message_id=msg.forwarded_from_message_id,
            forwarded_from_user_id=msg.forwarded_from_user_id,
            body_encrypted=body_encrypted,
        )

        msg_encr_dto = await self._message_service.save(encrypt_msg_dto)

        # Сохранение новых файлов
        files_data = []
        for file in files:
            file_id = uuid4()
            file_path = f'{self._config.upload_file_path}/{file_id}.dat'
            attachment_dto = MessageAttachmentSaveDTO(
                id=file_id,
                message_id=msg_encr_dto.id,
                file_name=file.filename or '',
                file_path=file_path,
                mime_type=file.content_type or '',
                size=file.size or 0
            )
            await self._message_service.add_attachment(attachment_dto)
            await self._file_storage.save_upload(file, file_path)
            files_data.append(
                {"id": str(file_id), "file_name": file.filename or '', "mime_type": file.content_type or '',
                 "size": file.size or 0})

        if files_data:
            msg_encr_dto = await self._message_service.get_with_rel(msg_encr_dto.id)

        # Расшифровываем сообщение в DTO
        msg_decrypt_dto = self._get_decrypt_msg_dto(msg_encr_dto)

        if msg.forwarded_from_message_id:
            old_msg_encr = await self._message_service.get_with_rel(msg.forwarded_from_message_id)
            old_msg_decrypt = self._get_decrypt_msg_dto(old_msg_encr)

            if old_msg_decrypt:
                if old_msg_decrypt.forwarded_from:
                    fwd_text = old_msg_decrypt.forwarded_from.text
                    fwd_files = old_msg_decrypt.forwarded_from.files
                    original_chat_id = old_msg_encr.forwarded_from.chat_id
                else:
                    fwd_text = old_msg_decrypt.text
                    fwd_files = old_msg_decrypt.files
                    original_chat_id = old_msg_encr.chat_id

                if fwd_files:
                    for old_file in fwd_files:
                        new_attachment_dto = MessageAttachmentSaveDTO(
                            id=uuid4(),
                            message_id=msg_encr_dto.id,
                            file_name=old_file.file_name,
                            file_path=old_file.file_path,
                            mime_type=old_file.mime_type,
                            size=old_file.size
                        )
                        await self._message_service.add_attachment(new_attachment_dto)

                    msg_encr_dto = await self._message_service.get_with_rel(msg_encr_dto.id)
                    msg_decrypt_dto = self._get_decrypt_msg_dto(msg_encr_dto)

                msg_decrypt_dto.forwarded_from = ForwardedMessageDTO(
                    forwarded_from_message_id=msg.forwarded_from_message_id,
                    forwarded_from_user_id=old_msg_decrypt.sender_id or "",
                    type=old_msg_decrypt.type,
                    text=fwd_text,
                    files=fwd_files,
                    chat_id=original_chat_id
                )

        await self._chat_service.update(chat.id, ChatUpdateDTO(
            last_message_id=msg_encr_dto.id,
            last_message_at=msg_encr_dto.created_at
        ))

        members = await self._chat_service.get_members(chat.id)
        for member in members:
            if member.user_id == actor_id:
                continue
            self._uow.add_after_commit(
                lambda uid=member.user_id: self._unread_cache.incr(chat_id=chat.id, user_id=uid)
            )

        msg_data = self._to_pub_broker(msg_decrypt_dto)

        if is_new_chat and msg.recipient_id:
            self._uow.add_after_commit(
                lambda: self._ws_broker.publish_join_chat(
                    action_type="join_chat",
                    chat_id=chat.id,
                    user_id=msg.recipient_id
                )
            )
            self._uow.add_after_commit(
                lambda: self._ws_broker.publish_join_chat(
                    action_type="join_chat",
                    chat_id=chat.id,
                    user_id=actor_id
                )
            )
            self._uow.add_after_commit(
                lambda: self._ws_broker.publish_to_user(
                    action_type="new_chat",
                    user_id=msg.recipient_id,
                    data={"chat_id": str(chat.id)}
                )
            )
            self._uow.add_after_commit(
                lambda: self._ws_broker.publish_to_user(
                    action_type="message",
                    user_id=msg.recipient_id,
                    data=msg_data
                )
            )
            self._uow.add_after_commit(
                lambda: self._ws_broker.publish_to_chat(
                    action_type="message",
                    chat_id=chat.id,
                    data=msg_data
                )
            )
        else:
            self._uow.add_after_commit(
                lambda: self._ws_broker.publish_to_chat(
                    action_type="message",
                    chat_id=chat.id,
                    data=msg_data
                )
            )

        self._uow.add_event(AuditEvent(
            actor_type=ActionType.SEND_MESSAGE,
            actor_id=actor_id,
            target_id=str(msg_decrypt_dto.id),
            old_data=None,
            new_data={"chat_id": str(chat.id), "text_length": len(msg.text or ""), "type": msg.type.value},
            context=Context(ip=request_meta.ip, user_agent=request_meta.user_agent, source=request_meta.source),
            occurred_at=datetime.now(tz=timezone.utc),
        ))

        return msg_decrypt_dto

    async def _get_or_create_private_chat(self, user_1: str, user_2: str) -> ChatDTO:
        chat = await self._chat_service.find_between_users(user_1, user_2)
        if chat:
            return chat

        chat_id = uuid4()
        new_chat = await self._chat_service.save(ChatSaveDTO(id=chat_id, type=ChatType.PRIVATE))
        await self._chat_service.add_member(ChatMemberSaveDTO(chat_id=chat_id, user_id=user_1, role=ChatRole.MEMBER))
        await self._chat_service.add_member(ChatMemberSaveDTO(chat_id=chat_id, user_id=user_2, role=ChatRole.MEMBER))
        return new_chat

    @staticmethod
    def _to_pub_broker(msg_decrypt_dto: MessageGetDTO) -> dict:
        reply_to = None
        forwarded_from = None
        files_data = []

        # Обрабатываем обычные файлы
        if msg_decrypt_dto.files:
            for f in msg_decrypt_dto.files:
                files_data.append({
                    "id": str(f.id),
                    "file_name": f.file_name,
                    "mime_type": f.mime_type,
                    "size": f.size,
                    "created_at": f.created_at.isoformat() if f.created_at else None,
                    "updated_at": f.updated_at.isoformat() if f.updated_at else None,
                })

        # Обрабатываем ответ (reply)
        if msg_decrypt_dto.reply_to:
            reply_to = {
                'id': str(msg_decrypt_dto.reply_to.id),
                'type': msg_decrypt_dto.reply_to.type.value if hasattr(msg_decrypt_dto.reply_to.type, 'value') else msg_decrypt_dto.reply_to.type,
                'text': msg_decrypt_dto.reply_to.text
            }

        # Обрабатываем пересылку (forward)
        if msg_decrypt_dto.forwarded_from:
            fwd = msg_decrypt_dto.forwarded_from
            fwd_files_data = []
            if fwd.files:
                for f in fwd.files:
                    fwd_files_data.append({
                        "id": str(f.id),
                        "file_name": f.file_name,
                        "mime_type": f.mime_type,
                        "size": f.size,
                        "created_at": f.created_at.isoformat() if f.created_at else None,
                        "updated_at": f.updated_at.isoformat() if f.updated_at else None,
                    })

            forwarded_from = {
                'forwarded_from_message_id': str(fwd.forwarded_from_message_id),
                'forwarded_from_user_id': fwd.forwarded_from_user_id,
                'type': fwd.type.value if hasattr(fwd.type, 'value') else fwd.type,
                'text': fwd.text,
                'files': fwd_files_data,
                'chat_id': str(fwd.chat_id) if fwd.chat_id else ""
            }

        # Собираем итоговый словарь
        data = {
            "id": str(msg_decrypt_dto.id),
            "chat_id": str(msg_decrypt_dto.chat_id),
            "sender_id": msg_decrypt_dto.sender_id,
            'reply_to': reply_to,
            'forwarded_from': forwarded_from,
            "text": msg_decrypt_dto.text,
            "created_at": msg_decrypt_dto.created_at.isoformat() if msg_decrypt_dto.created_at else None,
            'files': files_data
        }
        return data

    def _get_decrypt_msg_dto(self, msg_encr_dto: MessageEncryptedGetDTO) -> MessageGetDTO:
        reply_msg_dto, forward_msg_dto = None, None
        reply_text_decrypt, forward_text_decrypt, msg_text_decrypt = None, None, None

        if msg_encr_dto.reply_to and msg_encr_dto.reply_to.body_encrypted:
            reply_text_decrypt = self._encoder.decrypt(msg_encr_dto.reply_to.body_encrypted)
        if msg_encr_dto.forwarded_from and msg_encr_dto.forwarded_from.body_encrypted:
            forward_text_decrypt = self._encoder.decrypt(msg_encr_dto.forwarded_from.body_encrypted)
        if msg_encr_dto.body_encrypted:
            msg_text_decrypt = self._encoder.decrypt(msg_encr_dto.body_encrypted)

        if msg_encr_dto.reply_to:
            encr_reply = msg_encr_dto.reply_to
            reply_msg_dto = ReplyMessageDTO(id=encr_reply.id, type=encr_reply.type, text=reply_text_decrypt)

        if msg_encr_dto.forwarded_from:
            encr_forwarded_from = msg_encr_dto.forwarded_from
            fwd_files = encr_forwarded_from.files
            forward_msg_dto = ForwardedMessageDTO(
                forwarded_from_message_id=encr_forwarded_from.forwarded_from_message_id,
                forwarded_from_user_id=encr_forwarded_from.forwarded_from_user_id,
                type=encr_forwarded_from.type,
                text=forward_text_decrypt,
                files=fwd_files,
                chat_id=encr_forwarded_from.chat_id
            )

        return MessageGetDTO(
            id=msg_encr_dto.id,
            chat_id=msg_encr_dto.chat_id,
            sender_id=msg_encr_dto.sender_id,
            type=msg_encr_dto.type,
            text=msg_text_decrypt,
            reply_to=reply_msg_dto,
            forwarded_from=forward_msg_dto,
            is_edited=msg_encr_dto.is_edited,
            created_at=msg_encr_dto.created_at,
            updated_at=msg_encr_dto.updated_at,
            files=msg_encr_dto.files
        )