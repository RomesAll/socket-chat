from datetime import datetime, timezone
from uuid import uuid4
from app.business_logic.services import UserService, VerificationService, ChatService
from app.business_logic.unit_of_work import UnitOfWork
from app.domain.events.audit import AuditEvent, Context
from app.domain.events.enums import ActionType
from app.infrastructure.email import EmailSender
from app.shared.dto.audit import RequestMeta
from app.shared.dto.auth import LoginOrRegisterDtoResponse
from app.shared.dto.chat import ChatSaveDTO, ChatMemberSaveDTO
from app.shared.dto.enums import SendType, ChatType
from app.shared.dto.user import UserSaveDTO, UserEncryptedSaveDTO
from app.shared.log_config import LogMixin


class RegisterUserUseCase(LogMixin):
    """
    Регистрация нового пользователя.

    Сценарий:
    - Сохранить пользователя (пароль хешируется).
    - Сгенерировать код подтверждения.
    - Сохранить код в Redis.
    - Записать audit-событие.
    - Отправить код по email.
    """

    def __init__(
        self,
        user_service: UserService,
        chat_service: ChatService,
        verification_service: VerificationService,
        email_sender: EmailSender,
        uow: UnitOfWork,
    ):
        self._user_service = user_service
        self._verification_service = verification_service
        self._email_sender = email_sender
        self._chat_service = chat_service
        self._uow = uow

    async def execute(
        self,
        request: UserSaveDTO,
        request_meta: RequestMeta,
    ) -> LoginOrRegisterDtoResponse:
        time_now = datetime.now(tz=timezone.utc)

        # Сохранить пользователя
        encrypt_psw = self._user_service.hash_password(request.password)
        user = await self._user_service.save(UserEncryptedSaveDTO(
            id=request.id,
            display_name=request.display_name,
            email=request.email,
            avatar_url=request.avatar_url,
            description=request.description,
            years_old=request.years_old,
            role=request.role,
            password=encrypt_psw
        ))

        # Сгенерировать и сохранить код
        code = await self._verification_service.generate_and_save(user.id)

        # Сохранить audit событие
        self._uow.add_event(AuditEvent(
            actor_type=ActionType.CREATE_NEW_USER,
            actor_id=user.id,
            target_id=user.id,
            old_data=None,
            new_data={
                "email": user.email,
                "role": user.role.value,
            },
            context=Context(
                ip=request_meta.ip,
                user_agent=request_meta.user_agent,
                source=request_meta.source,
            ),
            occurred_at=time_now,
        ))

        # Добавить чат по умолчанию для пользователя
        default_chat = await self._chat_service.save(ChatSaveDTO(
            id=uuid4(),
            type=ChatType.PRIVATE,
        ))
        await self._chat_service.add_member(ChatMemberSaveDTO(
            chat_id=default_chat.id,
            user_id=request.id
        ))

        # Отправка кода подтверждения после commit
        self._uow.add_after_commit(
            lambda: self._email_sender.send_accept_code(user.email, str(code))
        )

        self.log_info(f"Зарегистрирован пользователь {user.id}")
        return LoginOrRegisterDtoResponse(
            send_code=SendType.EMAIL,
            time_send=time_now,
        )