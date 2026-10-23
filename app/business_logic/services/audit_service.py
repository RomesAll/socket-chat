from app.infrastructure.mongo.audit.repositories import AuditRepository
from app.domain.events.enums import ActionType


class AuditService:
    """Сервис для чтения audit-событий."""

    def __init__(self, repo: AuditRepository):
        self._repo = repo

    @staticmethod
    def _serialize(events: list[dict]) -> list[dict]:
        for e in events:
            if "_id" in e:
                e["_id"] = str(e["_id"])
        return events

    async def get_by_actor(self, actor_id: str, limit: int = 100, offset: int = 0) -> list[dict]:
        return self._serialize(await self._repo.find_by_actor(actor_id, limit, offset))

    async def get_by_target(self, action: ActionType, target_id: str, limit: int = 100, offset: int = 0) -> list[dict]:
        return self._serialize(await self._repo.find_by_target(action, target_id, limit, offset))

    async def get_by_action(self, action: ActionType | None, days: int = 30, limit: int = 1000, offset: int = 0) -> \
    list[dict]:
        if action is None:
            return self._serialize(await self._repo.find_all(days, limit, offset))
        return self._serialize(await self._repo.find_by_action(action, days, limit, offset))

    async def get_by_request_id(self, request_id: str) -> list[dict]:
        return self._serialize(await self._repo.find_by_request_id(request_id))

    async def get_by_actor_target(self, actor_id: str, target: str, days: int = 30) -> list[dict]:
        return self._serialize(await self._repo.find_by_actor_target(actor_id, target, days))