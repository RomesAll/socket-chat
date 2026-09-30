from uuid import uuid4, UUID
from fastapi import UploadFile
import aiofiles
from app.business_logic.exceptions import UnsupportedFileTypeError
from app.data_layer.models.messages import MimeType
from app.shared.config import get_config
from app.shared.dto.message import MessageAttachmentsDtoPostRequest


class FileManager:
    """Менеджер для потокового чтенеия-записи файла"""
    @classmethod
    async def read_file(cls, file_path, chunk_size: int = 65536):
        """Генератор для потокового чтения из файла"""
        async with aiofiles.open(file_path, mode="rb") as f:
            while True:
                chunk = await f.read(chunk_size)
                if not chunk:
                    break
                yield chunk

    @classmethod
    async def read_upload_file_in_chunks(cls, upload_file: UploadFile, chunk_size: int = 65536):
        """Генератор для потокового чтения из UploadFile Fastapi"""
        while True:
            chunk = await upload_file.read(chunk_size)
            if not chunk:
                break
            yield chunk

    @classmethod
    async def write_file(cls, path_to_save: str, file: UploadFile, chunk_size: int = 65536):
        """Функция для потокового сохранения"""
        async with aiofiles.open(path_to_save, mode="wb") as f:
            async for chunk in cls.read_upload_file_in_chunks(file, chunk_size):
                await f.write(chunk)

    @classmethod
    async def upload_file(
            cls,
            upload_file:  list[UploadFile],
            message_id: UUID
    ):
        """Функция загрузки файлов на сервер"""
        for file in upload_file:
            if not file.filename or not file.size:
                continue
            file_id = uuid4()
            file_path = get_config().upload_file_path
            try:
                mime_type = MimeType(file.content_type)
            except ValueError:
                raise UnsupportedFileTypeError(
                    f"Тип файла {file.content_type} не поддерживается"
                )
            dto_file = MessageAttachmentsDtoPostRequest(
                id=file_id,
                file_name=file.filename,
                file_path=file_path,
                file_size=file.size,
                message_id=message_id,
                mime_type=mime_type
            )
            await cls.write_file(
                path_to_save=f'{file_path}/{file.filename}',
                file=file
            )
            yield dto_file