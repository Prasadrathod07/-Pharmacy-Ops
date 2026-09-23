"""Integration tests for order creation, transactional fulfilment, and the
state machine (master spec §11, §32, §37, Prompt 06 — Appendix A scenarios).

Each test creates its own throwaway drug/inventory so it never depends on
or mutates the shared seeded demo dataset's stock levels.
"""
import pytest
from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.main import app
from app.models import Drug, Inventory, InventoryTransaction, Order, OrderItem, Patient

client = TestClient(app)


@pytest.fixture()
def stocked_drug():
    """A drug with 50 units on hand."""
    setup = SessionLocal()
    try:
        drug = Drug(code="ORDER-TEST-STOCKED", name="Order Test Stocked Drug")
        setup.add(drug)
        setup.flush()
        setup.add(Inventory(drug_id=drug.id, quantity_on_hand=50, low_stock_threshold=10, reorder_threshold=5))
        setup.commit()
        drug_id = drug.id
    finally:
        setup.close()

    yield drug_id
    _cleanup_drug(drug_id)


@pytest.fixture()
def empty_drug():
    """A drug with 0 units on hand (out of stock)."""
    setup = SessionLocal()
    try:
        drug = Drug(code="ORDER-TEST-EMPTY", name="Order Test Empty Drug")
        setup.add(drug)
        setup.flush()
        setup.add(Inventory(drug_id=drug.id, quantity_on_hand=0, low_stock_threshold=10, reorder_threshold=5))
        setup.commit()
        drug_id = drug.id
    finally:
        setup.close()

    yield drug_id
    _cleanup_drug(drug_id)


@pytest.fixture()
def inactive_drug():
    setup = SessionLocal()
    try:
        drug = Drug(code="ORDER-TEST-INACTIVE", name="Order Test Inactive Drug", is_active=False)
        setup.add(drug)
        setup.flush()
        setup.add(Inventory(drug_id=drug.id, quantity_on_hand=100, low_stock_threshold=10, reorder_threshold=5))
        setup.commit()
        drug_id = drug.id
    finally:
        setup.close()

    yield drug_id
    _cleanup_drug(drug_id)


@pytest.fixture()
def two_stocked_drugs():
    """One drug with plenty of stock, one with none - for mixed-availability orders."""
    setup = SessionLocal()
    try:
        available = Drug(code="ORDER-TEST-MIX-AVAILABLE", name="Mix Available Drug")
        unavailable = Drug(code="ORDER-TEST-MIX-UNAVAILABLE", name="Mix Unavailable Drug")
        setup.add_all([available, unavailable])
        setup.flush()
        setup.add(Inventory(drug_id=available.id, quantity_on_hand=50, low_stock_threshold=10, reorder_threshold=5))
        setup.add(Inventory(drug_id=unavailable.id, quantity_on_hand=0, low_stock_threshold=10, reorder_threshold=5))
        setup.commit()
        ids = (available.id, unavailable.id)
    finally:
        setup.close()

    yield ids
    _cleanup_drug(ids[0])
    _cleanup_drug(ids[1])


def _cleanup_drug(drug_id: int) -> None:
    """Deletes a throwaway drug and everything created against it during the test.

    Orders are discovered via OrderItem (not InventoryTransaction), since a
    WAITING_FOR_STOCK item never gets a transaction row but still holds an
    FK to the drug that would otherwise block deleting it.
    """
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
            # Deletes ALL transactions/items of this order (covers sibling
            # drugs in a mixed multi-item order too), not just this drug's.
            cleanup.query(InventoryTransaction).filter_by(order_id=order.id).delete()
            for item in list(order.items):
                cleanup.delete(item)
            cleanup.delete(order)
            cleanup.flush()
            remaining = cleanup.query(Order).filter_by(patient_id=patient_id).count()
            if remaining == 0:
                patient = cleanup.get(Patient, patient_id)
                if patient is not None:
                    cleanup.delete(patient)
        cleanup.query(InventoryTransaction).filter_by(drug_id=drug_id).delete()
        cleanup.query(Inventory).filter_by(drug_id=drug_id).delete()
        cleanup.query(Drug).filter_by(id=drug_id).delete()
        cleanup.commit()
    finally:
        cleanup.close()


class TestCreateOrderValidation:
    def test_missing_patient_name_rejected(self, stocked_drug):
        response = client.post("/api/v1/orders", json={"patient_name": "   ", "items": [{"drug_id": stocked_drug, "quantity": 1}]})
        assert response.status_code == 422

    def test_patient_name_is_trimmed(self, stocked_drug):
        response = client.post(
            "/api/v1/orders", json={"patient_name": "  Padded Name  ", "items": [{"drug_id": stocked_drug, "quantity": 1}]}
        )
        assert response.status_code == 201
        assert response.json()["patient_name"] == "Padded Name"

    def test_empty_items_rejected(self):
        response = client.post("/api/v1/orders", json={"patient_name": "No Items", "items": []})
        assert response.status_code == 422

    def test_zero_quantity_rejected(self, stocked_drug):
        response = client.post(
            "/api/v1/orders", json={"patient_name": "Zero Qty", "items": [{"drug_id": stocked_drug, "quantity": 0}]}
        )
        assert response.status_code == 422

    def test_negative_quantity_rejected(self, stocked_drug):
        response = client.post(
            "/api/v1/orders", json={"patient_name": "Neg Qty", "items": [{"drug_id": stocked_drug, "quantity": -3}]}
        )
        assert response.status_code == 422

    def test_nonexistent_drug_rejected(self):
        response = client.post(
            "/api/v1/orders", json={"patient_name": "Bad Drug", "items": [{"drug_id": 999999999, "quantity": 1}]}
        )
        assert response.status_code == 400
        assert response.json()["error"]["code"] == "DRUG_NOT_FOUND"

    def test_inactive_drug_rejected(self, inactive_drug):
        response = client.post(
            "/api/v1/orders", json={"patient_name": "Inactive Drug Patient", "items": [{"drug_id": inactive_drug, "quantity": 1}]}
        )
        assert response.status_code == 400
        assert response.json()["error"]["code"] == "DRUG_INACTIVE"

    def test_duplicate_drug_line_rejected(self, stocked_drug):
        response = client.post(
            "/api/v1/orders",
            json={
                "patient_name": "Dup Patient",
                "items": [{"drug_id": stocked_drug, "quantity": 1}, {"drug_id": stocked_drug, "quantity": 2}],
            },
        )
        assert response.status_code == 422


class TestCreateOrderFulfilment:
    def test_sufficient_stock_dispenses_immediately(self, stocked_drug):
        response = client.post(
            "/api/v1/orders", json={"patient_name": "Sufficient Stock Patient", "items": [{"drug_id": stocked_drug, "quantity": 20}]}
        )
        assert response.status_code == 201
        body = response.json()
        assert body["status"] == "DISPENSED"
        assert body["dispensed_at"] is not None
        assert body["items"][0]["status"] == "DISPENSED"
        assert body["items"][0]["dispensed_quantity"] == 20

        inv_response = client.get(f"/api/v1/inventory/{stocked_drug}")
        assert inv_response.json()["quantity_on_hand"] == 30

    def test_zero_stock_order_goes_waiting_without_negative_inventory(self, empty_drug):
        response = client.post(
            "/api/v1/orders", json={"patient_name": "Zero Stock Patient", "items": [{"drug_id": empty_drug, "quantity": 5}]}
        )
        assert response.status_code == 201
        body = response.json()
        assert body["status"] == "WAITING_FOR_STOCK"
        assert body["items"][0]["status"] == "WAITING_FOR_STOCK"
        assert body["items"][0]["dispensed_quantity"] == 0

        inv_response = client.get(f"/api/v1/inventory/{empty_drug}")
        assert inv_response.json()["quantity_on_hand"] == 0

    def test_partially_insufficient_stock_goes_waiting(self, stocked_drug):
        response = client.post(
            "/api/v1/orders",
            json={"patient_name": "Partial Insufficient Patient", "items": [{"drug_id": stocked_drug, "quantity": 999}]},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["status"] == "WAITING_FOR_STOCK"
        assert body["items"][0]["dispensed_quantity"] == 0

        inv_response = client.get(f"/api/v1/inventory/{stocked_drug}")
        assert inv_response.json()["quantity_on_hand"] == 50  # untouched

    def test_multi_item_all_available_dispenses_whole_order(self, two_stocked_drugs):
        available_id, _ = two_stocked_drugs
        response = client.post(
            "/api/v1/orders",
            json={
                "patient_name": "Multi Available Patient",
                "items": [{"drug_id": available_id, "quantity": 10}],
            },
        )
        assert response.status_code == 201
        assert response.json()["status"] == "DISPENSED"

    def test_multi_item_one_unavailable_leaves_order_waiting_with_partial_dispense(self, two_stocked_drugs):
        available_id, unavailable_id = two_stocked_drugs
        response = client.post(
            "/api/v1/orders",
            json={
                "patient_name": "Multi Mixed Patient",
                "items": [
                    {"drug_id": available_id, "quantity": 10},
                    {"drug_id": unavailable_id, "quantity": 5},
                ],
            },
        )
        assert response.status_code == 201
        body = response.json()
        assert body["status"] == "WAITING_FOR_STOCK"

        by_drug = {item["drug_id"]: item for item in body["items"]}
        assert by_drug[available_id]["status"] == "DISPENSED"
        assert by_drug[unavailable_id]["status"] == "WAITING_FOR_STOCK"

        # The available item's stock WAS deducted even though the order overall waits.
        inv_response = client.get(f"/api/v1/inventory/{available_id}")
        assert inv_response.json()["quantity_on_hand"] == 40

    def test_dispense_creates_inventory_ledger_entry(self, stocked_drug):
        response = client.post(
            "/api/v1/orders", json={"patient_name": "Ledger Check Patient", "items": [{"drug_id": stocked_drug, "quantity": 15}]}
        )
        order_id = response.json()["id"]

        txn_response = client.get(f"/api/v1/inventory/{stocked_drug}/transactions")
        transactions = txn_response.json()["items"]
        dispense_txn = next(t for t in transactions if t["movement_type"] == "DISPENSE")
        assert dispense_txn["order_id"] == order_id
        assert dispense_txn["quantity_delta"] == -15
        assert dispense_txn["quantity_before"] == 50
        assert dispense_txn["quantity_after"] == 35
        assert dispense_txn["source"] == "NEW_ORDER"

    def test_reused_patient_name_maps_to_same_patient(self, stocked_drug):
        r1 = client.post("/api/v1/orders", json={"patient_name": "Repeat Visitor", "items": [{"drug_id": stocked_drug, "quantity": 1}]})
        r2 = client.post("/api/v1/orders", json={"patient_name": "Repeat Visitor", "items": [{"drug_id": stocked_drug, "quantity": 1}]})
        assert r1.json()["patient_id"] == r2.json()["patient_id"]

    def test_order_numbers_are_unique(self, stocked_drug):
        r1 = client.post("/api/v1/orders", json={"patient_name": "Number Check A", "items": [{"drug_id": stocked_drug, "quantity": 1}]})
        r2 = client.post("/api/v1/orders", json={"patient_name": "Number Check B", "items": [{"drug_id": stocked_drug, "quantity": 1}]})
        assert r1.json()["order_number"] != r2.json()["order_number"]


class TestOrderStateMachine:
    def test_complete_dispensed_order_succeeds(self, stocked_drug):
        create = client.post("/api/v1/orders", json={"patient_name": "Complete Flow Patient", "items": [{"drug_id": stocked_drug, "quantity": 5}]})
        order_id = create.json()["id"]

        response = client.post(f"/api/v1/orders/{order_id}/complete")
        assert response.status_code == 200
        assert response.json()["status"] == "COMPLETED"
        assert response.json()["completed_at"] is not None

    def test_double_complete_rejected(self, stocked_drug):
        create = client.post("/api/v1/orders", json={"patient_name": "Double Complete Patient", "items": [{"drug_id": stocked_drug, "quantity": 5}]})
        order_id = create.json()["id"]
        client.post(f"/api/v1/orders/{order_id}/complete")

        response = client.post(f"/api/v1/orders/{order_id}/complete")
        assert response.status_code == 409
        assert response.json()["error"]["code"] == "INVALID_STATE_TRANSITION"

    def test_cannot_complete_a_waiting_order_directly(self, empty_drug):
        create = client.post("/api/v1/orders", json={"patient_name": "Waiting Complete Patient", "items": [{"drug_id": empty_drug, "quantity": 5}]})
        order_id = create.json()["id"]

        response = client.post(f"/api/v1/orders/{order_id}/complete")
        assert response.status_code == 409

    def test_complete_nonexistent_order_returns_404(self):
        response = client.post("/api/v1/orders/999999999/complete")
        assert response.status_code == 404
        assert response.json()["error"]["code"] == "ORDER_NOT_FOUND"

    def test_cancel_waiting_order_succeeds(self, empty_drug):
        create = client.post("/api/v1/orders", json={"patient_name": "Cancel Waiting Patient", "items": [{"drug_id": empty_drug, "quantity": 5}]})
        order_id = create.json()["id"]

        response = client.post(f"/api/v1/orders/{order_id}/cancel")
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "CANCELLED"
        assert body["cancelled_at"] is not None
        assert body["items"][0]["status"] == "CANCELLED"

    def test_cannot_cancel_a_completed_order(self, stocked_drug):
        create = client.post("/api/v1/orders", json={"patient_name": "Cancel Completed Patient", "items": [{"drug_id": stocked_drug, "quantity": 5}]})
        order_id = create.json()["id"]
        client.post(f"/api/v1/orders/{order_id}/complete")

        response = client.post(f"/api/v1/orders/{order_id}/cancel")
        assert response.status_code == 409

    def test_cancel_nonexistent_order_returns_404(self):
        response = client.post("/api/v1/orders/999999999/cancel")
        assert response.status_code == 404
