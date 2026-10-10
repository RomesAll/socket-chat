from typing import Protocol
from uuid import uuid4, UUID
import aiofiles
from app.business_logic.exceptions import UnsupportedFileTypeError
from app.shared.dto.enums import MimeType
from app.shared.dto.message import MessageAttachmentSaveDTO
from app.shared.config import get_config


class UploadFileProtocol(Protocol):
    """Минимальный контракт загружаемого файла."""

    filename: str | None
    size: int | None
    content_type: str | None

    async def read(self, size: int = -1) -> bytes: ...


class FileManager:
    """Менеджер для потокового чтения-записи файла."""

    @classmethod
    async def read_file(cls, file_path: str, chunk_size: int = 65536):
        """Генератор для потокового чтения из файла."""
        async with aiofiles.open(file_path, mode="rb") as f:
            while True:
                chunk = await f.read(chunk_size)
                if not chunk:
                    break
                yield chunk

    @classmethod
    async def read_in_chunks(
        cls, upload_file: UploadFileProtocol, chunk_size: int = 65536,
    ):
        """Генератор для потокового чтения из файла-источника."""
        while True:
            chunk = await upload_file.read(chunk_size)
            if not chunk:
                break
            yield chunk

    @classmethod
    async def write_file(
        cls,
        path_to_save: str,
        file: UploadFileProtocol,
        chunk_size: int = 65536,
    ) -> None:
        """Потоковое сохранение файла на диск."""
        async with aiofiles.open(path_to_save, mode="wb") as f:
            async for chunk in cls.read_in_chunks(file, chunk_size):
                await f.write(chunk)

    @classmethod
    async def upload_files(
        cls,
        upload_files: list[UploadFileProtocol],
        message_id: UUID,
    ):
        """Загрузка файлов на сервер. Генератор DTO."""
        for file in upload_files:
            if not file.filename or not file.size:
                continue

            try:
                mime_type = MimeType(file.content_type)
            except ValueError:
                raise UnsupportedFileTypeError(
                    f"Тип файла {file.content_type} не поддерживается"
                )

            file_id = uuid4()
            file_path = get_config().upload_file_path

            dto_file = MessageAttachmentSaveDTO(
                id=file_id,
                file_name=file.filename,
                file_path=file_path,
                size=file.size,
                message_id=message_id,
                mime_type=mime_type,
            )

            await cls.write_file(
                path_to_save=f"{file_path}/{file.filename}",
                file=file,
            )

            yield dto_file