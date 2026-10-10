from app.business_logic.file_manager import FileManager


async def test_read_wile(tmp_path):
    """Тест: Успешное чтение данных с файла."""
    file_path = tmp_path / "test.txt"
    file_path.write_text("hello world")
    read_file_data = []

    async for data in FileManager.read_file(file_path):
        read_file_data.append(data)

    assert len(read_file_data) == 1
    assert type(read_file_data[0]) is bytes
    assert read_file_data[0] == b'hello world'


async def test_write_file(tmp_path, fake_upload_file):
    """Тест: Успешная запись в файл."""
    path = tmp_path / "out.txt"
    file = fake_upload_file(b"hello world")
    await FileManager.write_file(str(path), file)

    assert path.read_bytes() == b"hello world"