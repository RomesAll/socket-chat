from app.shared.config import create_config, AppMode
import celery

config = create_config(AppMode.DEV)


celery_app = celery.Celery('celery_app', broker=config.redis.url)
celery_app.conf.update(
    result_backend=config.redis.url,
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],

    task_time_limit=300,
    task_soft_time_limit=240,
    worker_prefetch_multiplier=5,

    timezone='Europe/Moscow',
    enable_utc=True,
    include = [
        'app.business_logic.tasks.outbox_event',
        'app.business_logic.tasks.history',
        'app.business_logic.tasks.statistics',
        'app.business_logic.tasks.email_sender',
    ]
)