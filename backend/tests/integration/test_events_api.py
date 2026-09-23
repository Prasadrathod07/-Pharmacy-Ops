"""Tests for the SSE stream generator (master spec §42, Prompt 14).

Deliberately does NOT drive this through TestClient's live streaming
transport: an infinite `while True` SSE generator combined with
TestClient's buffered streaming (httpx's ASGI transport, run in a
background thread) is a known hang risk documented for exactly this
pattern - breaking out of client-side iteration early doesn't reliably
tear down the server-side generator/task, and it hung indefinitely when
tried here. Testing the generator function directly is faster and immune
to that transport gotcha, while still exercising the real logic.

Route registration itself (path exists, wired into the router) is already
covered by the app-wide openapi.json route listing used elsewhere in this
suite; StreamingResponse's HTTP-level behavior is Starlette's, not ours.
"""
import asyncio

import pytest

from app.api.v1 import events as events_module
from app.core.config import get_settings
from app.events.publisher import EventBroadcaster


class _FakeRequest:
    """Reports disconnected after `disconnect_after` calls to is_disconnected()."""

    def __init__(self, disconnect_after: int) -> None:
        self._calls = 0
        self._disconnect_after = disconnect_after

    async def is_disconnected(self) -> bool:
        self._calls += 1
        return self._calls > self._disconnect_after


def test_first_yielded_message_is_the_connected_event():
    async def scenario():
        generator = events_module._event_stream(_FakeRequest(disconnect_after=0))
        first_message = await generator.__anext__()
        assert first_message == "event: connected\ndata: {}\n\n"
        await generator.aclose()

    asyncio.run(scenario())


def test_generator_exits_cleanly_when_client_disconnects():
    async def scenario():
        generator = events_module._event_stream(_FakeRequest(disconnect_after=0))
        await generator.__anext__()  # connected message
        with pytest.raises(StopAsyncIteration):
            await generator.__anext__()  # is_disconnected() now True -> loop breaks

    asyncio.run(scenario())


def test_generator_delivers_a_published_event_then_disconnects(monkeypatch):
    fresh_broadcaster = EventBroadcaster()
    monkeypatch.setattr(events_module, "broadcaster", fresh_broadcaster)
    monkeypatch.setattr(get_settings(), "enable_realtime", True)

    async def scenario():
        fresh_broadcaster.bind_loop(asyncio.get_running_loop())
        request = _FakeRequest(disconnect_after=1)
        generator = events_module._event_stream(request)

        await generator.__anext__()  # connected message; this is also where subscribe() happens

        fresh_broadcaster.publish("order.updated", {"order_id": 99})

        message = await generator.__anext__()
        assert "event: order.updated" in message
        assert '"order_id": 99' in message

        with pytest.raises(StopAsyncIteration):
            await generator.__anext__()

    asyncio.run(scenario())


def test_generator_unsubscribes_on_close():
    async def scenario():
        fresh_broadcaster = EventBroadcaster()
        events_stream_module_broadcaster_backup = events_module.broadcaster
        events_module.broadcaster = fresh_broadcaster
        try:
            generator = events_module._event_stream(_FakeRequest(disconnect_after=0))
            await generator.__anext__()
            assert len(fresh_broadcaster._subscribers) == 1

            with pytest.raises(StopAsyncIteration):
                await generator.__anext__()

            assert len(fresh_broadcaster._subscribers) == 0
        finally:
            events_module.broadcaster = events_stream_module_broadcaster_backup

    asyncio.run(scenario())
