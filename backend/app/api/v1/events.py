"""Server-Sent Events stream (master spec §42).

Purely a UI refresh hint. Nothing here is authoritative - if this stream
is never opened, drops mid-request, or ENABLE_REALTIME is off, every other
endpoint keeps working exactly as before.
"""
import asyncio
import logging

from fastapi import APIRouter, Request
from starlette.responses import StreamingResponse

from app.events.publisher import broadcaster

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/events", tags=["events"])

KEEPALIVE_SECONDS = 15


async def _event_stream(request: Request):
    queue = broadcaster.subscribe()
    try:
        yield "event: connected\ndata: {}\n\n"
        while True:
            if await request.is_disconnected():
                break
            try:
                event_type, payload = await asyncio.wait_for(queue.get(), timeout=KEEPALIVE_SECONDS)
                yield f"event: {event_type}\ndata: {payload}\n\n"
            except asyncio.TimeoutError:
                yield ": keep-alive\n\n"
    finally:
        broadcaster.unsubscribe(queue)


@router.get("/stream", summary="Live event stream (SSE, optional)")
async def stream_events(request: Request) -> StreamingResponse:
    """Server-Sent Events stream emitting `order.created`, `order.updated`,
    `inventory.updated`, and `dashboard.updated` as UI refresh hints - never
    authoritative data, and safe to ignore entirely. Delivers nothing but
    periodic keep-alive comments when `ENABLE_REALTIME` is off.
    """
    return StreamingResponse(
        _event_stream(request),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
