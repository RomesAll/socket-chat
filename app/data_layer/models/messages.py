from datetime import datetime
from pathlib import Path
from sqlalchemy import ForeignKey, DateTime, String
from sqlalchemy.orm import mapped_column, Mapped
from enum import Enum
from uuid import UUID
from .base import Base, UuidIsMixin


class MessageType(str, Enum):
    """Перечисление типов сообщений"""
    TEXT = 'text'
    FILE = 'file'
    SYSTEM = 'system'
    TEXT_AND_FILE = 'text_and_file'


class MimeType(str, Enum):
    # ===== Изображения =====
    PNG = "image/png"
    JPEG = "image/jpeg"
    GIF = "image/gif"
    BMP = "image/bmp"
    WEBP = "image/webp"
    SVG = "image/svg+xml"
    TIFF = "image/tiff"
    ICO = "image/vnd.microsoft.icon"
    AVIF = "image/avif"

    # ===== Текст =====
    PLAIN = "text/plain"
    HTML = "text/html"
    CSS = "text/css"
    CSV = "text/csv"
    XML = "text/xml"
    MARKDOWN = "text/markdown"

    # ===== JSON =====
    JSON = "application/json"

    # ===== PDF =====
    PDF = "application/pdf"

    # ===== JavaScript / TypeScript =====
    JS = "application/javascript"
    TS = "application/typescript"

    # ===== Офисные документы =====
    DOC = "application/msword"
    DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    XLS = "application/vnd.ms-excel"
    XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    PPT = "application/vnd.ms-powerpoint"
    PPTX = "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    ODT = "application/vnd.oasis.opendocument.text"
    ODS = "application/vnd.oasis.opendocument.spreadsheet"
    ODP = "application/vnd.oasis.opendocument.presentation"

    # ===== Архивы =====
    ZIP = "application/zip"
    RAR = "application/vnd.rar"
    GZIP = "application/gzip"
    TAR = "application/x-tar"
    SEVEN_Z = "application/x-7z-compressed"

    # ===== Видео =====
    MP4 = "video/mp4"
    WEBM = "video/webm"
    OGG_VIDEO = "video/ogg"
    QUICKTIME = "video/quicktime"
    AVI = "video/x-msvideo"
    MPEG = "video/mpeg"

    # ===== Аудио =====
    MP3 = "audio/mpeg"
    WAV = "audio/wav"
    OGG_AUDIO = "audio/ogg"
    FLAC = "audio/flac"
    AAC = "audio/aac"
    MIDI = "audio/midi"


class Message(UuidIsMixin, Base):
    """Orm модель для хранения информации о сообщениях"""
    chat_id: Mapped[UUID] = mapped_column(
        ForeignKey('chat.id', ondelete='CASCADE'),
    )
    sender_id: Mapped[str | None] = mapped_column(
        ForeignKey('user.id', ondelete='SET NULL'),
        nullable=True,
    )
    body_encrypted: Mapped[str]
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