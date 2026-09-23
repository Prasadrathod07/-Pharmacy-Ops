"""FIFO pending-order fulfilment tests (master spec §15, §15.1, Prompt 08).

Each test builds its own throwaway drug(s) with explicit `ordered_at`
timestamps so FIFO order is deterministic, then restocks and inspects the
resulting order/item states and inventory ledger.
"""
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.main import app
from app.models import Drug, Inventory, InventoryTransaction, Order, OrderItem, Patient

client = TestClient(app)

BASE_TIME = datetime(2026, 1, 1, tzinfo=timezone.utc)


def _make_drug(code: str, quantity_on_hand: int = 0, low: int = 5, reorder: int = 2) -> int:
    setup = SessionLocal()
    try:
        drug = Drug(code=code, name=f"Fulfilment Test {code}")
        setup.add(drug)
        setup.flush()
        setup.add(Inventory(drug_id=drug.id, quantity_on_hand=quantity_on_hand, low_stock_threshold=low, reorder_threshold=reorder))
        setup.commit()
        return drug.id
    finally:
        setup.close()


def _cleanup_drug(drug_id: int) -> None:
    cleanup = SessionLocal()
    try:
        order_ids = [
            row[0] for row in cleanup.query(OrderItem.order_id).filter(OrderItem.drug_id == drug_id).distinct().all()
        ]
        for order_id in order_ids:
            order = cleanup.get(Order, order_id)
            if order is None:
                continue
            patient_id = order.patient_id
            cleanup.query(InventoryTransaction).filter_by(order_id=order.id).delete()
            for item in list(order.items):
                cleanup.delete(item)
            cleanup.delete(order)
            cleanup.flush()
            if cleanup.query(Order).filter_by(patient_id=patient_id).count() == 0:
                patient = cleanup.get(Patient, patient_id)
                if patient is not None:
                    cleanup.delete(patient)
        cleanup.query(InventoryTransaction).filter_by(drug_id=drug_id).delete()
        cleanup.query(Inventory).filter_by(drug_id=drug_id).delete()
        cleanup.query(Drug).filter_by(id=drug_id).delete()
        cleanup.commit()
    finally:
        cleanup.close()


def _create_waiting_order(drug_id: int, patient_name: str, quantity: int, ordered_at: datetime):
    response = client.post(
        "/api/v1/orders",
        json={
            "patient_name": patient_name,
            "ordered_at": ordered_at.isoformat(),
            "items": [{"drug_id": drug_id, "quantity": quantity}],
        },
    )
    assert response.status_code == 201
    assert response.json()["status"] == "WAITING_FOR_STOCK"
    return response.json()


@pytest.fixture()
def fifo_drug():
    drug_id = _make_drug("FULFIL-TEST-FIFO")
    yield drug_id
    _cleanup_drug(drug_id)


class TestFifoPendingFulfilment:
    def test_spec_example_101_102_103_restock_35(self, fifo_drug):
        """Exact master spec §15.1 example: waiting 10/20/20, restock +35 ->
        first two fulfilled, third stays waiting, remaining stock = 5.
        """
        order_101 = _create_waiting_order(fifo_drug, "FIFO Patient 101", 10, BASE_TIME)
        order_102 = _create_waiting_order(fifo_drug, "FIFO Patient 102", 20, BASE_TIME + timedelta(minutes=1))
        order_103 = _create_waiting_order(fifo_drug, "FIFO Patient 103", 20, BASE_TIME + timedelta(minutes=2))

        restock_response = client.post(f"/api/v1/inventory/{fifo_drug}/restock", json={"quantity": 35})
        assert restock_response.status_code == 200
        assert restock_response.json()["quantity_on_hand"] == 5

        r101 = client.get(f"/api/v1/orders/{order_101['id']}").json()
        r102 = client.get(f"/api/v1/orders/{order_102['id']}").json()
        r103 = client.get(f"/api/v1/orders/{order_103['id']}").json()

        assert r101["status"] == "DISPENSED"
        assert r101["items"][0]["dispensed_quantity"] == 10
        assert r101["dispensed_at"] is not None

        assert r102["status"] == "DISPENSED"
        assert r102["items"][0]["dispensed_quantity"] == 20

        assert r103["status"] == "WAITING_FOR_STOCK"
        assert r103["items"][0]["dispensed_quantity"] == 0

    def test_does_not_skip_ahead_to_a_smaller_later_order(self, fifo_drug):
        """A big order blocking the front of the FIFO queue must not be
        skipped in favor of a smaller order behind it, even if the smaller
        one could otherwise be fulfilled.
        """
        big_order = _create_waiting_order(fifo_drug, "FIFO Big Order", 100, BASE_TIME)
        small_order = _create_waiting_order(fifo_drug, "FIFO Small Order", 1, BASE_TIME + timedelta(minutes=1))

        client.post(f"/api/v1/inventory/{fifo_drug}/restock", json={"quantity": 50})

        big = client.get(f"/api/v1/orders/{big_order['id']}").json()
        small = client.get(f"/api/v1/orders/{small_order['id']}").json()

        assert big["status"] == "WAITING_FOR_STOCK"
        assert small["status"] == "WAITING_FOR_STOCK"  # never touched, despite being fulfillable

        inv = client.get(f"/api/v1/inventory/{fifo_drug}").json()
        assert inv["quantity_on_hand"] == 50  # untouched

    def test_single_pending_order_exact_restock(self, fifo_drug):
        order = _create_waiting_order(fifo_drug, "FIFO Exact Patient", 10, BASE_TIME)

        client.post(f"/api/v1/inventory/{fifo_drug}/restock", json={"quantity": 10})

        result = client.get(f"/api/v1/orders/{order['id']}").json()
        assert result["status"] == "DISPENSED"

        inv = client.get(f"/api/v1/inventory/{fifo_drug}").json()
        assert inv["quantity_on_hand"] == 0

    def test_insufficient_restock_leaves_order_waiting(self, fifo_drug):
        order = _create_waiting_order(fifo_drug, "FIFO Insufficient Patient", 10, BASE_TIME)

        client.post(f"/api/v1/inventory/{fifo_drug}/restock", json={"quantity": 5})

        result = client.get(f"/api/v1/orders/{order['id']}").json()
        assert result["status"] == "WAITING_FOR_STOCK"

        inv = client.get(f"/api/v1/inventory/{fifo_drug}").json()
        assert inv["quantity_on_hand"] == 5  # restocked but not consumed

    def test_excess_restock_leaves_surplus(self, fifo_drug):
        order = _create_waiting_order(fifo_drug, "FIFO Excess Patient", 10, BASE_TIME)

        client.post(f"/api/v1/inventory/{fifo_drug}/restock", json={"quantity": 50})

        result = client.get(f"/api/v1/orders/{order['id']}").json()
        assert result["status"] == "DISPENSED"

        inv = client.get(f"/api/v1/inventory/{fifo_drug}").json()
        assert inv["quantity_on_hand"] == 40

    def test_ledger_entry_has_correct_source_and_amounts(self, fifo_drug):
        _create_waiting_order(fifo_drug, "FIFO Ledger Patient", 10, BASE_TIME)

        client.post(f"/api/v1/inventory/{fifo_drug}/restock", json={"quantity": 10})

        txns = client.get(f"/api/v1/inventory/{fifo_drug}/transactions").json()["items"]
        pending_fulfilment_txns = [t for t in txns if t["source"] == "PENDING_FULFILMENT"]
        assert len(pending_fulfilment_txns) == 1
        txn = pending_fulfilment_txns[0]
        assert txn["movement_type"] == "DISPENSE"
        assert txn["quantity_delta"] == -10
        assert txn["quantity_before"] == 10
        assert txn["quantity_after"] == 0

    def test_no_double_fulfilment_on_repeated_restock(self, fifo_drug):
        order = _create_waiting_order(fifo_drug, "FIFO No Double Patient", 10, BASE_TIME)

        client.post(f"/api/v1/inventory/{fifo_drug}/restock", json={"quantity": 10})
        client.post(f"/api/v1/inventory/{fifo_drug}/restock", json={"quantity": 10})  # unrelated second restock

        result = client.get(f"/api/v1/orders/{order['id']}").json()
        assert result["items"][0]["dispensed_quantity"] == 10  # not 20

        txns = client.get(f"/api/v1/inventory/{fifo_drug}/transactions").json()["items"]
        pending_fulfilment_txns = [t for t in txns if t["source"] == "PENDING_FULFILMENT"]
        assert len(pending_fulfilment_txns) == 1

        inv = client.get(f"/api/v1/inventory/{fifo_drug}").json()
        assert inv["quantity_on_hand"] == 10  # first restock consumed, second sits unconsumed


@pytest.fixture()
def two_drugs_for_multi_item():
    drug_a = _make_drug("FULFIL-TEST-MULTI-A", quantity_on_hand=50)  # plenty, for immediate dispense
    drug_b = _make_drug("FULFIL-TEST-MULTI-B", quantity_on_hand=0)  # none, will wait then get restocked
    yield drug_a, drug_b
    _cleanup_drug(drug_a)
    _cleanup_drug(drug_b)


class TestMultiItemOrderRecomputation:
    def test_order_transitions_to_dispensed_once_last_waiting_item_is_fulfilled(self, two_drugs_for_multi_item):
        drug_a, drug_b = two_drugs_for_multi_item

        response = client.post(
            "/api/v1/orders",
            json={
                "patient_name": "Multi Item Recompute Patient",
                "items": [
                    {"drug_id": drug_a, "quantity": 5},  # dispensed immediately
                    {"drug_id": drug_b, "quantity": 10},  # waits
                ],
            },
        )
        assert response.status_code == 201
        order_id = response.json()["id"]
        assert response.json()["status"] == "WAITING_FOR_STOCK"

        by_drug = {item["drug_id"]: item for item in response.json()["items"]}
        assert by_drug[drug_a]["status"] == "DISPENSED"
        assert by_drug[drug_b]["status"] == "WAITING_FOR_STOCK"

        client.post(f"/api/v1/inventory/{drug_b}/restock", json={"quantity": 10})

        final = client.get(f"/api/v1/orders/{order_id}").json()
        assert final["status"] == "DISPENSED"
        assert final["dispensed_at"] is not None
        for item in final["items"]:
            assert item["status"] == "DISPENSED"
