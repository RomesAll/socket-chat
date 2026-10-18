from datetime import datetime, timezone
from uuid import uuid4, UUID
from app.business_logic.exceptions import RefreshTokenInActive
from app.infrastructure.security.jwt_manager import JWTFacade
from app.infrastructure.redis import JWTWhiteListCache
from app.shared.dto.enums import RoleEnum
from app.shared.dto.jwt import JWTTokenResponse, JWTRefreshTokenResponse
from app.shared.log_config import LogMixin


class TokenService(LogMixin):
    """
    Операции над агрегатом Token (jwt токенами для auth).
    """

    def __init__(
        self,
        jwt_white_list: JWTWhiteListCache,
        jwt_facade: type[JWTFacade],
    ):
        self._jwt_white_list = jwt_white_list
        self._jwt_facade = jwt_facade

    async def create_jwt_auth_tokens(
        self, user_id: str, sub: str, role: RoleEnum,
    ) -> JWTTokenResponse:
        """
        Создать новую пару access и refresh токенов.

        Алгоритм:\n
        - Генерирует ID refresh токена.
        - Генерирует пару access и refresh токенов.
        - Высчитывает время истечения срока токена для белых списков.
        - Сохраняет ID refresh токена в белый список.
        - Возвращает DTO с парой access и refresh токенов.
        """
        refresh_token_id = uuid4()
        jwt_tokens = self._jwt_facade.create_tokens(
            user_id=user_id,
            sub=sub,
            role=role,
            refresh_id=refresh_token_id,
        )

        ex = int(
            (datetime.now(tz=timezone.utc) + JWTFacade.jwt_refresh_manager.EXPIRES_DELTA).timestamp()
        )
        await self._jwt_white_list.save_refresh_token(
            user_id=user_id,
            token_id=refresh_token_id,
            ex=ex,
        )

        return JWTTokenResponse(
            refresh_token=jwt_tokens.refresh_token,
            access_token=jwt_tokens.access_token,
        )

    async def refresh_jwt_auth_tokens(
        self, refresh_token: JWTRefreshTokenResponse,
    ) -> JWTTokenResponse:
        """
        Обновить пару access и refresh токенов.

        Алгоритм:\n
        - Проверить активность refresh токена.
        - Удалить старый ID refresh токена.
        - Сгенерировать новый ID refresh токена.
        - Сгенерировать пару access и refresh токенов.
        - Высчитать время истечения срока токена для белых списков.
        - Сохранить ID refresh токена в белый список.
        - Вернуть DTO с парой access и refresh токенов.
        """
        is_active = await self._jwt_white_list.is_token_active(
            user_id=refresh_token.user_id,
            token_id=refresh_token.refresh_id,
        )
        if not is_active:
            self.log_warning(
                f"Попытка использовать неактивный refresh токен: "
                f"user_id={refresh_token.user_id}, refresh_id={refresh_token.refresh_id}"
            )
            raise RefreshTokenInActive(refresh_token.user_id, refresh_token.refresh_id)

        await self._jwt_white_list.delete_refresh_token(
            user_id=refresh_token.user_id,
            token_id=refresh_token.refresh_id,
        )

        return await self.create_jwt_auth_tokens(
            user_id=refresh_token.user_id,
            sub=refresh_token.sub,
            role=refresh_token.role,
        )

    async def is_active(self, user_id: str, refresh_id: UUID) -> bool:
        """
        Проверить, что refresh токен активен (не отозван).

        Алгоритм:\n
        - Делегирует проверку в JWTWhiteListCache.
        - Возвращает True, если токен есть в white list.
        """
        return await self._jwt_white_list.is_token_active(user_id, refresh_id)

    async def revoke(self, user_id: str, refresh_id: UUID) -> None:
        """
        Отозвать конкретный refresh токен.

        Алгоритм:\n
        - Удаляет refresh_id из white list.
        - Логирует факт отзыва.
        """
        await self._jwt_white_list.delete_refresh_token(user_id, refresh_id)
        self.log_info(f"Отозван refresh токен: user_id={user_id}, refresh_id={refresh_id}")

    async def revoke_all(self, user_id: str, exclude_token_ids: set[UUID] | None = None) -> None:
        """
        Отозвать все refresh токены пользователя.

        Алгоритм:\n
        - Удаляет все refresh_id пользователя из white list.
        - Логирует факт отзыва.
        """
        await self._jwt_white_list.clear_user_token(user_id, exclude_token_ids)
        self.log_info(f"Отозваны все refresh токены пользователя {user_id}")