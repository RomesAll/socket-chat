from app.business_logic.services import UserService
from app.infrastructure.email import EmailSender
from app.shared.log_config import LogMixin


class SendEmailMessage(LogMixin):
    """Отправить сообщения по email"""

    def __init__(
        self,
        email_sender: EmailSender,
        user_service: UserService
    ):
        self._email_sender = email_sender
        self._user_service = user_service

    async def execute(self, user_id: str, actor_id: str, msg: str):
        user_email = (await self._user_service.get(user_id)).email
        await self._email_sender.send_message(
            sender_id=actor_id,
            to=user_email,
            msg=msg
        )