import asyncio
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


class EventBus:
    def __init__(self):
        self._subscribers: list[asyncio.Queue] = []

    def subscribe(self) -> asyncio.Queue:
        queue: asyncio.Queue = asyncio.Queue()
        self._subscribers.append(queue)
        logger.debug("Client subscribed to event bus", subscriber_count=len(self._subscribers))
        return queue

    def unsubscribe(self, queue: asyncio.Queue):
        if queue in self._subscribers:
            self._subscribers.remove(queue)
            logger.debug("Client unsubscribed from event bus", subscriber_count=len(self._subscribers))

    async def publish(self, event: dict[str, Any]):
        for queue in self._subscribers:
            await queue.put(event)

    def publish_nowait(self, event: dict[str, Any]):
        for queue in self._subscribers:
            try:
                queue.put_nowait(event)
            except asyncio.QueueFull:
                pass

    @property
    def subscriber_count(self) -> int:
        return len(self._subscribers)


_event_bus: EventBus | None = None


def get_event_bus() -> EventBus:
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus
