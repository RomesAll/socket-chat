from datetime import date
from uuid import UUID
from fastapi import APIRouter, Depends, Form, UploadFile, File, HTTPException, status
from pydantic import BaseModel
from starlette.responses import FileResponse
from app.business_logic.exceptions import (
    PermissionError,
    TargetSendNotFound,
    ReplyMessageForwardedError,
    UserIsNotMember,
)
from app.business_logic.use_cases.message.get_file_path import GetFilePathUseCase
from app.business_logic.use_cases.message.send_email_message import SendEmailMessage
from app.di.dependencies import get_email_sender
from app.infrastructure.database.exceptions import DBError, RecordNotFound
from app.infrastructure.email import EmailSender
from app.presentation_layer.rest_api.commands.messages import (
    SendMessageCommand
)
from app.business_logic.use_cases.message import (
    SendMessageUseCase,
    DeleteMessageUseCase,
    GetChatHistoryUseCase,
    MarkMessagesReadUseCase,
)
from app.di.auth import get_access_payload, get_request_meta, get_user_id, require_admins
from app.di.use_cases import (
    get_send_message_use_case,
    get_delete_message_use_case,
    get_chat_history_use_case,
    get_mark_messages_read_use_case, get_file_path_use_case, get_send_email_use_case,
)
from app.shared.dto.audit import RequestMeta
from app.shared.dto.chat import ChatMemberDTO
from app.shared.dto.enums import MessageType
from app.shared.dto.message import MessageGetDTO, SendMessage

router = APIRouter(prefix="/messages", tags=["messages"])


class EmailMessage(BaseModel):
    message: str


@router.post("")
async def send_message(
    chat_id: UUID | None = Form(None),
    recipient_id: str | None = Form(None),
    message_type: str = Form(...),
    text: str | None = Form(None),
    reply_to_message_id: UUID | None = Form(None),
    forwarded_from_message_id: UUID | None = Form(None),
    forwarded_from_user_id: str | None = Form(None),
    files: list[UploadFile] = File(default=[]),
    payload = Depends(get_access_payload),
    request_meta: RequestMeta = Depends(get_request_meta),
    use_case: SendMessageUseCase = Depends(get_send_message_use_case),
):
    cmd = SendMessageCommand(
        chat_id=chat_id,
        recipient_id=recipient_id,
        type=MessageType(message_type),
        text=text,
        reply_to_message_id=reply_to_message_id,
        forwarded_from_user_id=forwarded_from_user_id,
        forwarded_from_message_id=forwarded_from_message_id
    )
    try:
        return await use_case.execute(SendMessage(**cmd.model_dump(exclude_unset=True)), files, payload.user_id, request_meta)
    except TargetSendNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Получатель или чат не найден")
    except ReplyMessageForwardedError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Нельзя ответить на пересланное сообщение")
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Внутренняя ошибка при отправке сообщения")


@router.get("/chats/{chat_id}", response_model=list[MessageGetDTO])
async def get_chat_history(
    chat_id: UUID,
    limit: int = 50,
    before_id: UUID | None = None,
    payload = Depends(get_access_payload),
    use_case: GetChatHistoryUseCase = Depends(get_chat_history_use_case),
):
    try:
        return await use_case.execute(
            chat_id=chat_id,
            limit=limit,
            before_id=before_id,
            actor_id=payload.user_id
        )
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Чат не найден или недоступен")


@router.get('/chats/{chat_id}/downloads/{file_id}')
async def download_files(
    file_id: UUID,
    chat_id: UUID,
    user_id: str = Depends(get_user_id),
    use_case = Depends(get_file_path_use_case)
):
    try:
        file_info = await use_case.execute(file_id=file_id, chat_id=chat_id, user_id=user_id)
        return FileResponse(
            path=file_info.file_path,
            media_type=file_info.mime_type or 'application/octet-stream',
            filename=file_info.file_name
        )
    except DBError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Файл не найден в базе данных")
    except FileNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Файл не найден на диске")
    except UserIsNotMember:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет доступа к этому файлу")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка при скачивании файла")


@router.delete("/{message_id}")
async def delete_message(
    message_id: UUID,
    payload = Depends(get_access_payload),
    request_meta: RequestMeta = Depends(get_request_meta),
    use_case: DeleteMessageUseCase = Depends(get_delete_message_use_case),
):
    try:
        return await use_case.execute(message_id, payload.user_id, request_meta)
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except RecordNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Сообщение не найдено")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Не удалось удалить сообщение")


@router.post("/{message_id}/read", response_model=ChatMemberDTO)
async def mark_read(
    message_id: UUID,
    chat_id: UUID,
    payload = Depends(get_access_payload),
    use_case: MarkMessagesReadUseCase = Depends(get_mark_messages_read_use_case),
):
    try:
        return await use_case.execute(chat_id, message_id, payload.user_id)
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Не удалось отметить сообщение прочитанным")


@router.post('/{user_id}/email', dependencies=[Depends(require_admins)])
async def send_email(
    user_id: str,
    cmd: EmailMessage,
    actor_id: str = Depends(get_user_id),
    use_case: SendEmailMessage = Depends(get_send_email_use_case)
):
    try:
        await use_case.execute(user_id, actor_id, cmd.message)
        return {'detail': 'ok'}
    except DBError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Не удалось отправить email")