from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RequestMeta:
    """Метаинформация запроса"""
    ip: str = 'unknown'
    user_agent: str = 'unknown'
    source: str = 'unknown'