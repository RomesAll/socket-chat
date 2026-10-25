from dataclasses import Field, is_dataclass
from typing import Callable, Protocol, ClassVar, Any


class DataclassInstance(Protocol):
    __dataclass_fields__: ClassVar[dict[str, Field[Any]]]


class EventRegistry:
    """
    Реестр обработчиков доменных событий.

    Хранит тип события: список обработчиков.
    Публикует событие всем подписчикам.
    """

    def __init__(self):
        self._handlers: dict[type, list[Callable]] = dict()

    def sub[D: DataclassInstance](self, event_type: type[D], handler: Callable):
        self._handlers.setdefault(event_type, []).append(handler)

    async def pub[D: DataclassInstance](self, event_payload: D):
        if not is_dataclass(event_payload):
            raise TypeError(f"Модель события {type(event_payload).__name__} должна быть датаклассом")

        handlers = self._handlers.get(type(event_payload), [])
        for handler in handlers:
            await handler(event_payload)