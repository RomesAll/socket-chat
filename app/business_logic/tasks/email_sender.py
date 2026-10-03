from datetime import datetime, timezone
from bson import ObjectId
from pymongo import MongoClient
from app.business_logic.email_sender import EmailSender
from app.data_layer.models.events import Status
from app.shared.celery_app import celery_app
from app.shared.config import get_config


@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=10,
    autoretry_for=(TimeoutError, ConnectionError),
    retry_backoff=True,
    retry_jitter=True,
)
def send_verify_code_email(self, to: str, code: int):
    """Отправляет код подтверждения и обновляет статус события"""
    config = get_config()
    sender = EmailSender(
        smtp_server=config.smtp.server,
        port=config.smtp.port,
        sender_email=config.smtp.gmail,
        password=config.smtp.app_psw,
    )
    sender.send_accept_code(to=to, code=str(code))
    return {"to": to, "status": "sent"}