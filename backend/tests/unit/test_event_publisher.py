"""Unit tests for the in-process SSE broadcaster (master spec §42, Prompt 14).

Publishing must never be able to break the caller - these tests focus on
that guarantee, plus the ENABLE_REALTIME on/off behaviour, rather than the
network transport (covered separately in test_events_api.py).
"""
import asyncio

from app.core.config import get_settings
from app.events.publisher import EventBroadcaster


def test_publish_with_no_subscribers_or_bound_loop_does_not_raise():
    broadcaster = EventBroadcaster()
    broadcaster.publish("order.created", {"order_id": 1})  # no loop bound, no subscribers


def test_publish_is_noop_when_realtime_disabled(monkeypatch):
    monkeypatch.setattr(get_settings(), "enable_realtime", False)

    async def scenario():
        broadcaster = EventBroadcaster()
        broadcaster.bind_loop(asyncio.get_running_loop())
        queue = broadcaster.subscribe()

        broadcaster.publish("order.created", {"order_id": 42})
        await asyncio.sleep(0.05)

        assert queue.empty()

    asyncio.run(scenario())


def test_publish_delivers_to_subscriber_when_realtime_enabled(monkeypatch):
    monkeypatch.setattr(get_settings(), "enable_realtime", True)

    async def scenario():
        broadcaster = EventBroadcaster()
        broadcaster.bind_loop(asyncio.get_running_loop())
        queue = broadcaster.subscribe()

        broadcaster.publish("order.created", {"order_id": 42, "status": "DISPENSED"})

        event_type, payload = await asyncio.wait_for(queue.get(), timeout=1)
        assert event_type == "order.created"
        assert '"order_id": 42' in payload
        assert '"status": "DISPENSED"' in payload

    asyncio.run(scenario())


def test_unsubscribed_queue_receives_nothing_further(monkeypatch):
    monkeypatch.setattr(get_settings(), "enable_realtime", True)

    async def scenario():
        broadcaster = EventBroadcaster()
        broadcaster.bind_loop(asyncio.get_running_loop())
        queue = broadcaster.subscribe()
        broadcaster.unsubscribe(queue)

        broadcaster.publish("order.created", {"order_id": 1})
        await asyncio.sleep(0.05)

        assert queue.empty()

    asyncio.run(scenario())


def test_publish_to_multiple_subscribers_delivers_to_all(monkeypatch):
    monkeypatch.setattr(get_settings(), "enable_realtime", True)

    async def scenario():
        broadcaster = EventBroadcaster()
        broadcaster.bind_loop(asyncio.get_running_loop())
        queue_a = broadcaster.subscribe()
        queue_b = broadcaster.subscribe()

        broadcaster.publish("inventory.updated", {"drug_id": 7})

        result_a = await asyncio.wait_for(queue_a.get(), timeout=1)
        result_b = await asyncio.wait_for(queue_b.get(), timeout=1)
        assert result_a == result_b

    asyncio.run(scenario())
