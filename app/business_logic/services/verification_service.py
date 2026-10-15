from app.infrastructure.security.code_generator import SecretsCodeGenerator
from app.infrastructure.redis import VerifyCodeStorage


class VerificationService:
    """
    Операции над агрегатом Verification (кодами подтверждения).
    """

    def __init__(self, storage: VerifyCodeStorage, generator: SecretsCodeGenerator):
        self._storage = storage
        self._generator = generator

    async def generate_and_save(self, user_id: str) -> int:
        code = self._generator.generate()
        await self._storage.save(user_id, code)
        return code

    async def validate(self, user_id: str, code: int) -> bool:
        return await self._storage.validate_code(user_id, code)