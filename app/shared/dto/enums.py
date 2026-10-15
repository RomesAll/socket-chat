from enum import Enum


class TokenType(str, Enum):
    """Перечисления типов токенов"""
    ACCESS_TOKEN = 'access_token'
    REFRESH_TOKEN = 'refresh_token'


class SendType(str, Enum):
    """Причисление с типом отправки кода"""
    EMAIL = 'email'


class ChatType(str, Enum):
    """Перечисление типов чатов"""
    PRIVATE = 'private'
    ROOM = 'room'


class ChatRole(str, Enum):
    """Перечисление ролей в комнатах"""
    OWNER = 'owner'
    ADMIN = 'admin'
    MEMBER = 'member'


class RoleEnum(str, Enum):
    """Перечисление списка ролей"""
    DEFAULT_USER = 'default_user'
    ADMIN = 'admin'
    SUPER_ADMIN = 'super_admin'


class MessageType(str, Enum):
    """Перечисление типов сообщений"""
    TEXT = 'text'
    FILE = 'file'
    SYSTEM = 'system'
    TEXT_AND_FILE = 'text_and_file'


class MimeType(str, Enum):
    """Перечисление mime типов"""
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