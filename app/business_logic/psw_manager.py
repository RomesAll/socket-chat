import bcrypt


class PasswordManager:
    """Класс менеджер для хеширования и проверки паролей"""
    @classmethod
    def hash_password(cls, psw: bytes) -> bytes:
        """Хеширование пароля"""
        salt = bcrypt.gensalt()
        hashed_psw = bcrypt.hashpw(psw, salt)
        return hashed_psw

    @classmethod
    def check_equal_psw(cls, password: bytes, hashed_password: bytes) -> bool:
        """Проверка паролей"""
        result: bool = bcrypt.checkpw(
            password,
            hashed_password
        )
        return result