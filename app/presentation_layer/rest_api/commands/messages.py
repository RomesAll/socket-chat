from uuid import UUID
from pydantic import BaseModel, Field, model_validator
from app.shared.dto.enums import MessageType


class SendMessageCommand(BaseModel):
    chat_id: UUID | None = Field(None)
    recipient_id: str | None = Field(None)
    type: MessageType = MessageType.TEXT
    text: str | None = Field(None, max_length=4000)
    reply_to_message_id: UUID | None = Field(None)
    forwarded_from_message_id: UUID | None = Field(None)
    forwarded_from_user_id: str | None = Field(None)

    @model_validator(mode="after")
    def check_target(self):
        if not self.chat_id and not self.recipient_id:
            raise ValueError("Нужен chat_id или recipient_id")
        if self.chat_id and self.recipient_id:
            raise ValueError("Только одно: chat_id или recipient_id")
        if self.type == MessageType.TEXT and not self.text:
            raise ValueError("TEXT требует text")
        return self


class EditMessageCommand(BaseModel):
    text: str = Field(..., min_length=1, max_length=4000)


class ForwardMessageCommand(BaseModel):
    message_id: UUID
    target_chat_id: UUID