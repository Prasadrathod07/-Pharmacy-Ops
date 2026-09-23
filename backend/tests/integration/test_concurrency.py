"""Concurrency/oversell-protection tests (master spec §16, Appendix A
Scenario E, Prompt 07).

FastAPI dispatches sync `def` route handlers via a thread pool, and each
request gets its own DB session/connection through the `get_db` dependency,
so two `TestClient` calls launched from separate Python threads genuinely
race at the database's row-lock level - this is not simulated concurrency.
"""
import threading
from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.main import app
from app.models import Drug, Inventory, InventoryTransaction, Order, OrderItem, Patient

client = TestClient(app)


@pytest.fixture()
def limited_stock_drug():
    """Exactly 10 units on hand - the master spec's exact concurrency scenario."""
    setup = SessionLocal()
    try:
        drug = Drug(code="CONCURRENCY-TEST-DRUG", name="Concurrency Test Drug")
        setup.add(drug)
        setup.flush()
        setup.add(Inventory(drug_id=drug.id, quantity_on_hand=10, low_stock_threshold=5, reorder_threshold=2))
        setup.commit()
        drug_id = drug.id
    finally:
        setup.close()

    yield drug_id

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


def _create_order(drug_id: int, patient_name: str, quantity: int):
    return client.post("/api/v1/orders", json={"patient_name": patient_name, "items": [{"drug_id": drug_id, "quantity": quantity}]})


class TestConcurrentOversellProtection:
    def test_two_simultaneous_orders_cannot_both_take_8_from_stock_of_10(self, limited_stock_drug):
        """Master spec Appendix A Scenario E, exactly: stock=10, A requests 8, B requests 8."""
        barrier = threading.Barrier(2)

        def place_order(patient_name: str):
            barrier.wait()  # maximize the chance both requests overlap in time
            return _create_order(limited_stock_drug, patient_name, 8)

        with ThreadPoolExecutor(max_workers=2) as pool:
            future_a = pool.submit(place_order, "Concurrency Patient A")
            future_b = pool.submit(place_order, "Concurrency Patient B")
            response_a = future_a.result(timeout=30)
            response_b = future_b.result(timeout=30)

        assert response_a.status_code == 201
        assert response_b.status_code == 201

        statuses = {response_a.json()["status"], response_b.json()["status"]}
        # Exactly one of the two must have been fulfilled; the other must wait.
        assert statuses == {"DISPENSED", "WAITING_FOR_STOCK"}

        dispensed = response_a if response_a.json()["status"] == "DISPENSED" else response_b
        waiting = response_b if dispensed is response_a else response_a

        assert dispensed.json()["items"][0]["dispensed_quantity"] == 8
        assert waiting.json()["items"][0]["dispensed_quantity"] == 0

        inv_response = client.get(f"/api/v1/inventory/{limited_stock_drug}")
        final_quantity = inv_response.json()["quantity_on_hand"]
        assert final_quantity == 2  # 10 - 8, never negative, never double-deducted

        # Exactly one DISPENSE ledger entry, with correct before/after.
        txns_response = client.get(f"/api/v1/inventory/{limited_stock_drug}/transactions")
        dispense_txns = [t for t in txns_response.json()["items"] if t["movement_type"] == "DISPENSE"]
        assert len(dispense_txns) == 1
        assert dispense_txns[0]["quantity_before"] == 10
        assert dispense_txns[0]["quantity_after"] == 2
        assert dispense_txns[0]["quantity_delta"] == -8

    def test_many_concurrent_requests_never_oversell(self, limited_stock_drug):
        """5 concurrent requests for 3 units each against a stock of 10:
        at most 3 can succeed (9 units), never more, never negative.
        """
        barrier = threading.Barrier(5)

        def place_order(index: int):
            barrier.wait()
            return _create_order(limited_stock_drug, f"Concurrency Bulk Patient {index}", 3)

        with ThreadPoolExecutor(max_workers=5) as pool:
            futures = [pool.submit(place_order, i) for i in range(5)]
            responses = [f.result(timeout=30) for f in futures]

        assert all(r.status_code == 201 for r in responses)

        dispensed_count = sum(1 for r in responses if r.json()["status"] == "DISPENSED")
        waiting_count = sum(1 for r in responses if r.json()["status"] == "WAITING_FOR_STOCK")

        assert dispensed_count == 3  # floor(10 / 3)
        assert waiting_count == 2

        inv_response = client.get(f"/api/v1/inventory/{limited_stock_drug}")
        final_quantity = inv_response.json()["quantity_on_hand"]
        assert final_quantity == 1  # 10 - (3*3), never negative
        assert final_quantity >= 0
