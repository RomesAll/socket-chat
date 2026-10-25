from starlette.datastructures import UploadFile
import aiofiles


class AsyncFileAdapter:
    """Адаптер для асинхронного управления файлами на сервере."""

    async def save_upload(self, upload_file: UploadFile, path: str) -> None:
        """
        Принимает объект UploadFile (из FastAPI/Starlette) 
        и асинхронно сохраняет его чанками.
        """
        async with aiofiles.open(path, mode='wb') as destination:
            while chunk := await upload_file.read(65536):
                await destination.write(chunk)