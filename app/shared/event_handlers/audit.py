from app.domain.events.audit import AuditEvent
from app.infrastructure.mongo.audit.documents.audit_docs import ContextDoc, AuditDoc
from app.infrastructure.mongo.audit.repositories import AuditRepository


class SaveAuditEventToMongo:
    """Сохранить событие в аудит систему Mongodb."""

    def __init__(self, repo: AuditRepository):
        self._repo = repo

    async def handle(self, event: AuditEvent):
        save_doc = AuditDoc(
            actor_type=event.actor_type,
            actor_id=event.actor_id,
            target_id=event.target_id,
            old_data=event.old_data,
            new_data=event.new_data,
            occurred_at=event.occurred_at,
            context=ContextDoc(
                ip=event.context.ip,
                user_agent=event.context.user_agent,
                source=event.context.source
            )
        )
        await self._repo.insert(save_doc)