from collections import defaultdict
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable


logger = logging.getLogger(__name__)


@dataclass
class Event:
    name: str
    payload: dict
    created_at: datetime = field(default_factory=datetime.utcnow)


class EventBus:
    def __init__(self):
        self._subscribers: dict[str, list[Callable[[Event], list[str] | None]]] = (
            defaultdict(list)
        )

    def subscribe(self, event_name: str, handler: Callable[[Event], list[str] | None]):
        if handler in self._subscribers[event_name]:
            return
        self._subscribers[event_name].append(handler)

    def publish(self, event_name: str, payload: dict, **kwargs) -> list[str]:
        event = Event(name=event_name, payload=payload)
        handlers = self._subscribers[event_name]
        logger.info(
            "event_published",
            extra={
                "event_name": event_name,
                "handlers_count": len(handlers),
                "payload_keys": sorted(payload.keys()),
            },
        )
        messages: list[str] = []
        for handler in handlers:
            result = handler(event, **kwargs) or []
            messages.extend(result)
        return messages
