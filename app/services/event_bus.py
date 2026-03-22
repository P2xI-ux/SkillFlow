from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import Callable


@dataclass
class Event:
    name: str
    payload: dict
    created_at: datetime = datetime.utcnow()


class EventBus:
    def __init__(self):
        self._subscribers: dict[str, list[Callable[[Event], list[str] | None]]] = defaultdict(list)

    def subscribe(self, event_name: str, handler: Callable[[Event], list[str] | None]):
        self._subscribers[event_name].append(handler)

    def publish(self, event_name: str, payload: dict) -> list[str]:
        event = Event(name=event_name, payload=payload)
        messages: list[str] = []
        for handler in self._subscribers[event_name]:
            result = handler(event) or []
            messages.extend(result)
        return messages
