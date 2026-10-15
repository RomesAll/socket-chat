from pathlib import Path
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import mapped_column, Mapped
from uuid import UUID
from .base import Base, UuidIsMixin
from app.shared.dto.enums import MessageType


class Message(UuidIsMixin, Base):
    """Orm модель для хранения информации о сообщениях"""
    chat_id: Mapped[UUID] = mapped_column(
        ForeignKey('chat.id', ondelete='CASCADE'),
    )
    sender_id: Mapped[str | None] = mapped_column(
        ForeignKey('user.id', ondelete='SET NULL'),
        nullable=True,
    )
    body_encrypted: Mapped[bytes | None] = mapped_column(default=None, nullable=True)
    type: Mapped[MessageType]
    reply_to_message_id: Mapped[UUID] = mapped_column(default=None, nullable=True)
    forwarded_from_message_id: Mapped[UUID] = mapped_column(default=None, nullable=True)
    forwarded_from_user_id: Mapped[str | None] = mapped_column(
        ForeignKey('user.id', ondelete='SET NULL'),
        nullable=True,
    )
    is_edited: Mapped[bool] = mapped_column(default=False)


class MessageAttachment(UuidIsMixin, Base):
    """Orm модель для хранения информации о метаданных файла в сообщениях"""
    message_id: Mapped[UUID] = mapped_column(
        ForeignKey('message.id', ondelete='CASCADE'),
    )
    file_name: Mapped[str] = mapped_column(String(100))
    file_path: Mapped[str]
    mime_type: Mapped[str]
    size: Mapped[int]

    @property
    def file(self) -> Path:
        """Проверка и получение полного пути к файлу"""
        path = Path(f'{self.file_path}/{self.file_name}')
        if not path.exists():
            raise Exception
        return path