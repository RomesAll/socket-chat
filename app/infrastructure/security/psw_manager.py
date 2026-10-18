import bcrypt


class PasswordManager:
    """Класс менеджер для хеширования и проверки паролей"""
    @classmethod
    def hash_password(cls, psw: str) -> bytes:
        """Хеширование пароля"""
        salt = bcrypt.gensalt()
        hashed_psw = bcrypt.hashpw(psw.encode(), salt)
        return hashed_psw

    @classmethod
    def check_equal_psw(cls, password: str, hashed_password: bytes) -> bool:
        """Проверка паролей"""
        result: bool = bcrypt.checkpw(
            password.encode(),
            hashed_password
        )
        return result