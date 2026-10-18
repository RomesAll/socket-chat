from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RequestMeta:
    """Метаинформация запроса"""
    ip: str | None
    user_agent: str | None
    source: str | None