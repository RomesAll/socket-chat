from datetime import datetime
from pathlib import Path
from sqlalchemy import ForeignKey, DateTime, func, String
from sqlalchemy.orm import mapped_column, Mapped, relationship
from enum import Enum
from uuid import UUID
from .base import Base, UuidIsMixin, IntIdMixin


class MessageType(str, Enum):
    """Перечисление типов сообщений"""
    TEXT = 'text'
    FILE = 'file'
    SYSTEM = 'system'
    TEXT_AND_FILE = 'text_and_file'


class Message(UuidIsMixin, Base):
    """Orm модель для хранения информации о сообщениях"""
    chat_id: Mapped[UUID] = mapped_column(
        ForeignKey('chat.id', ondelete='CASCADE'),
    )
    sender_id: Mapped[str] = mapped_column(
        ForeignKey('user.id', ondelete='CASCADE'),
    )
    body_encrypted: Mapped[str]
    type: Mapped[MessageType]
    reply_to_message_id: Mapped[UUID] = mapped_column(default=None, nullable=True)
    forwarded_from_message_id: Mapped[UUID] = mapped_column(default=None, nullable=True)
    forwarded_from_user_id: Mapped[str] = mapped_column(
        ForeignKey('user.id', ondelete='CASCADE'),
        default=None,
        nullable=True
    )
    is_edited: Mapped[bool] = mapped_column(default=False)
    is_deleted: Mapped[bool] = mapped_column(default=False)
    deleted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    message_file: Mapped[list['MessageAttachment']] = relationship(back_populates='message_attachment', cascade='all, delete-orphan',)


class MessageAttachment(IntIdMixin, Base):
    """Orm модель для хранения информации о метаданных файла в сообщениях"""
    message_id: Mapped[UUID] = mapped_column(
        ForeignKey('message.id', ondelete='CASCADE'),
    )
    file_name: Mapped[str] = mapped_column(String(100))
    file_path: Mapped[str]
    mime_type: Mapped[str]
    size: Mapped[int]
    message_attachment: Mapped['Message'] = relationship(back_populates='message_file', cascade='all, delete-orphan',)

    @property
    def file(self) -> Path:
        """Проверка и получение полного пути к файлу"""
        path = Path(f'{self.file_path}/{self.file_name}')
        if not path.exists():
            raise Exception
        return path