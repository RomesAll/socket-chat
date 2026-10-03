from datetime import datetime, timezone
from bson import ObjectId
from pymongo import MongoClient
from app.data_layer.models.events import Status
from app.shared.celery_app import celery_app
from app.shared.config import get_config

_client = None
_collection_history = None


def get_collection():
    global _client, _collection_history
    if _collection_history is None:
        _client = MongoClient(get_config().mongodb.url)
        _collection_history = _client["messenger_db"]["history"]
    return _collection_history


@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=10,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
)
def save_history(self, type_action: str, payload: dict):
    """Celery задача для сохранения истории изменения объекта бд"""
    coll_history = get_collection()
    if not (created_at := payload.get('created_at')):
        created_at = datetime.now(tz=timezone.utc)
    coll_history.insert_one({
        'payload': payload,
        'type': type_action,
        'created_at': created_at
    })