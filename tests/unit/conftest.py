import pytest


class FakeUploadFile:
    def __init__(self, data: bytes, filename: str = "test.txt"):
        self._data = data
        self._pos = 0
        self.filename = filename
        self.size = len(data)
        self.content_type = "text/plain"

    async def read(self, size: int = -1) -> bytes:
        if size == -1:
            chunk = self._data[self._pos:]
            self._pos = len(self._data)
            return chunk
        chunk = self._data[self._pos:self._pos + size]
        self._pos += len(chunk)
        return chunk


@pytest.fixture(scope='function')
def fake_upload_file():
    """Фикстура для получения класса FakeUploadFile"""
    return FakeUploadFile