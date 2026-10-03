import asyncio
import logging
from mongotic.asyncio import create_async_engine, async_sessionmaker
from mongotic import select
from app.business_logic.tasks.email_sender import send_verify_code_email
from app.business_logic.tasks.history import save_history
from app.business_logic.tasks.statistics import update_statistics
from app.data_layer.models.events import OutboxEvent, Status, EventType
from app.shared.config import create_config, AppMode

logger = logging.getLogger(__name__)
engine = create_async_engine(host=create_config(AppMode.DEV).mongodb.url)
session_factory = async_sessionmaker(bind=engine)


async def relay_once(limit: int = 10) -> int:
    """
    Функция для получения событий со статусом NEW.
    Раз в несколько секунд отправляет запрос в хранилище событий и отправляет их
    в celery задачи на обработку
    """
    async with session_factory() as session:
        try:
            result = session.scalars(
                select(OutboxEvent)
                .where(OutboxEvent.status == Status.NEW)
                .limit(limit)
                .order_by(OutboxEvent.created_at)
            )
            events = await result.all()
            for event in events:
                try:
                    event.status = Status.PROCESSING
                    if event.type == EventType.SEND_VERIFY_CODE:
                        send_verify_code_email.delay(
                            to=event.payload['to'],
                            code=event.payload['code']
                        )
                    else:
                        update_statistics.delay(event.type, event.payload)
                        save_history.delay(event.type, event.payload)
                    event.status = Status.PROCESSED
                except Exception as exc:
                    event.status = Status.FAILED
                    event.error_message = str(exc)
            await session.commit()
            return len(events)
        except Exception as exc:
            session.rollback()


async def main():
    logger.info("Outbox relay started")
    while True:
        try:
            count = await relay_once(limit=10)
            if count:
                logger.info("Processed %d events", count)
        except Exception:
            logger.exception("relay_once failed")
        await asyncio.sleep(1)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())