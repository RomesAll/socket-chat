from app.business_logic.services import TokenService, UserService
from app.infrastructure.websocket import WSBroker
from app.shared.log_config import LogMixin


class RevokeAllUserTokens(LogMixin):
    """
    Отозвать все refresh токены. Отправить сигнал для disconnect пользователя
    """

    def __init__(
        self,
        token_service: TokenService,
        user_service: UserService,
        ws_broker: WSBroker,
    ):
        self._token_service = token_service
        self._ws_broker = ws_broker
        self._user_service = user_service

    async def execute(self, user_id, actor_id):
        actor = await self._user_service.get(actor_id)
        target = await self._user_service.get(user_id)

        if not actor.role.can_manage(target.role):
            self.log_warning(f"Пользователь {actor_id} не может отключить {user_id}")
            raise PermissionError(f"Пользователь {actor_id} не может отключить {user_id}")

        await self._token_service.revoke_all(user_id)

        await self._ws_broker.publish_to_user(
            action_type="force_logout",
            user_id=user_id,
            data={}
        )