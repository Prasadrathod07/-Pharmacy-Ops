"""In-process SSE event broadcaster (master spec §42).

No Redis: this is a single-process pub/sub used only to push optional,
best-effort UI refresh hints (order.created, order.updated,
inventory.updated, dashboard.updated). It is never the source of truth -
the database is - and publishing is designed to never be able to break the
request that triggers it (guarded by try/except, and a no-op when
ENABLE_REALTIME is off or nobody is subscribed).

Services run as synchronous code in FastAPI's worker thread pool, while
subscribers are asyncio.Queues owned by the event loop. `call_soon_threadsafe`
is what makes publish() safely callable from those worker threads.
"""
import asyncio
import json
import logging
from typing import Any

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class EventBroadcaster:
    def __init__(self) -> None:
        self._subscribers: set[asyncio.Queue] = set()
        self._loop: asyncio.AbstractEventLoop | None = None

    def bind_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop

    def subscribe(self) -> asyncio.Queue:
        queue: asyncio.Queue = asyncio.Queue(maxsize=100)
        self._subscribers.add(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue) -> None:
        self._subscribers.discard(queue)

    def publish(self, event_type: str, data: dict[str, Any]) -> None:
        """Best-effort, thread-safe, never raises into the caller."""
        if not get_settings().enable_realtime:
            return
        if not self._subscribers or self._loop is None:
            return

        try:
            payload = json.dumps(data, default=str)
        except (TypeError, ValueError):
            logger.exception("event_serialize_failed", extra={"event_type": event_type})
            return

        for queue in list(self._subscribers):
            try:
                self._loop.call_soon_threadsafe(_put_nowait_safe, queue, (event_type, payload))
            except RuntimeError:
                # Event loop already closed (e.g. during shutdown) - drop silently.
                logger.warning("event_publish_dropped_loop_closed", extra={"event_type": event_type})


def _put_nowait_safe(queue: asyncio.Queue, item: tuple[str, str]) -> None:
    try:
        queue.put_nowait(item)
    except asyncio.QueueFull:
        logger.warning("event_queue_full_dropping_oldest")
        try:
            queue.get_nowait()
            queue.put_nowait(item)
        except asyncio.QueueEmpty:
            pass


broadcaster = EventBroadcaster()
