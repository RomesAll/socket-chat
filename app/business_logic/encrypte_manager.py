from cryptography.fernet import Fernet, InvalidToken


class SymmetricEncode:
    """Менеджер для симметричного шифрования сообщений через алгоритм fernet"""
    def __init__(self, app_key: bytes):
        self._fernet = Fernet(app_key)

    def encrypt(self, message: str) -> bytes:
        """Шифрование сообщения"""
        token = self._fernet.encrypt(message.encode())
        return token

    def decrypt(self, token: bytes) -> str:
        """Расшифровка сообщения"""
        try:
            message = self._fernet.decrypt(token)
            return message.decode()
        except InvalidToken:
            raise