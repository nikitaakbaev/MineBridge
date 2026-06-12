"""WebSocket event bus for backend runtime updates."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class BackendEvent:
    """Event sent to Electron/React clients."""

    type: str
    payload: dict[str, Any]


class EventBus:
    """Fan out backend events to active WebSocket subscribers."""

    def __init__(self) -> None:
        self._subscribers: set[tuple[asyncio.Queue[BackendEvent], asyncio.AbstractEventLoop]] = (
            set()
        )

    async def subscribe(self) -> asyncio.Queue[BackendEvent]:
        queue: asyncio.Queue[BackendEvent] = asyncio.Queue()
        self._subscribers.add((queue, asyncio.get_running_loop()))
        return queue

    def unsubscribe(self, queue: asyncio.Queue[BackendEvent]) -> None:
        for subscriber in tuple(self._subscribers):
            if subscriber[0] is queue:
                self._subscribers.discard(subscriber)

    def publish(self, event_type: str, **payload: Any) -> None:
        event = BackendEvent(type=event_type, payload=payload)
        for queue, loop in tuple(self._subscribers):
            loop.call_soon_threadsafe(queue.put_nowait, event)
