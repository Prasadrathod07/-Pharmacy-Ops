"""Integration tests for the inventory API (master spec §33, Prompt 04).

Runs against the real database; uses the seeded demo drugs (app.seed) as
fixtures via a client-scoped seed call, and creates its own throwaway
drug/inventory rows (via db_session, rolled back per test) for restock and
edge-case tests so they never mutate the shared seeded dataset.
"""
import pytest
from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.main import app
from app.models import Drug, Inventory, InventoryTransaction
from app.seed import run_seed

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def ensure_seed_data():
    run_seed()


class TestListInventory:
    def test_list_returns_all_seeded_drugs(self):
        response = client.get("/api/v1/inventory", params={"page_size": 50})
        assert response.status_code == 200
        body = response.json()
        codes = {item["drug_code"] for item in body["items"]}
        assert "PARACETAMOL-500-TAB" in codes
        assert body["total"] >= 8

    @pytest.mark.parametrize(
        "code,expected_status",
        [
            ("PARACETAMOL-500-TAB", "HEALTHY"),
            ("AMOXICILLIN-500-CAP", "LOW_STOCK"),
            ("AZITHROMYCIN-250-TAB", "CRITICAL"),
            ("METFORMIN-500-TAB", "OUT_OF_STOCK"),
        ],
    )
    def test_stock_status_calculation(self, code, expected_status):
        response = client.get("/api/v1/inventory", params={"search": code, "page_size": 5})
        assert response.status_code == 200
        items = response.json()["items"]
        assert len(items) == 1
        assert items[0]["status"] == expected_status

    def test_search_filters_by_name(self):
        response = client.get("/api/v1/inventory", params={"search": "paracetamol"})
        items = response.json()["items"]
        assert len(items) == 1
        assert items[0]["drug_code"] == "PARACETAMOL-500-TAB"

    def test_low_stock_only_filter(self):
        response = client.get("/api/v1/inventory", params={"low_stock_only": True, "page_size": 50})
        items = response.json()["items"]
        assert len(items) >= 1
        for item in items:
            assert item["status"] in ("LOW_STOCK", "CRITICAL", "OUT_OF_STOCK")

    def test_critical_only_filter_excludes_out_of_stock(self):
        response = client.get("/api/v1/inventory", params={"critical_only": True, "page_size": 50})
        items = response.json()["items"]
        assert len(items) >= 1
        for item in items:
            assert item["status"] == "CRITICAL"
            assert item["quantity_on_hand"] > 0

    def test_pagination(self):
        page_1 = client.get("/api/v1/inventory", params={"page": 1, "page_size": 3}).json()
        page_2 = client.get("/api/v1/inventory", params={"page": 2, "page_size": 3}).json()
        assert len(page_1["items"]) == 3
        assert page_1["page"] == 1
        assert page_2["page"] == 2
        ids_1 = {i["drug_id"] for i in page_1["items"]}
        ids_2 = {i["drug_id"] for i in page_2["items"]}
        assert ids_1.isdisjoint(ids_2)

    def test_sort_by_quantity_desc(self):
        response = client.get(
            "/api/v1/inventory", params={"sort_by": "quantity_on_hand", "sort_order": "desc", "page_size": 50}
        )
        quantities = [item["quantity_on_hand"] for item in response.json()["items"]]
        assert quantities == sorted(quantities, reverse=True)


class TestInventoryDetail:
    def test_get_detail_for_seeded_drug(self):
        list_response = client.get("/api/v1/inventory", params={"search": "PARACETAMOL-500-TAB"})
        drug_id = list_response.json()["items"][0]["drug_id"]

        response = client.get(f"/api/v1/inventory/{drug_id}")
        assert response.status_code == 200
        body = response.json()
        assert body["drug_code"] == "PARACETAMOL-500-TAB"
        assert len(body["recent_transactions"]) >= 1

    def test_get_detail_for_nonexistent_drug_returns_404(self):
        response = client.get("/api/v1/inventory/999999999")
        assert response.status_code == 404
        assert response.json()["error"]["code"] == "DRUG_NOT_FOUND"


class TestInventoryTransactions:
    def test_list_transactions_for_nonexistent_drug_returns_404(self):
        response = client.get("/api/v1/inventory/999999999/transactions")
        assert response.status_code == 404

    def test_list_transactions_paginated(self):
        list_response = client.get("/api/v1/inventory", params={"search": "PARACETAMOL-500-TAB"})
        drug_id = list_response.json()["items"][0]["drug_id"]

        response = client.get(f"/api/v1/inventory/{drug_id}/transactions", params={"page_size": 1})
        assert response.status_code == 200
        body = response.json()
        assert len(body["items"]) == 1
        assert body["total"] >= 1


@pytest.fixture()
def throwaway_drug() -> Drug:
    """A committed drug+inventory row, since the API under test runs in its
    own session/connection and must see it. Cleaned up explicitly afterward.
    """
    setup = SessionLocal()
    try:
        drug = Drug(code="RESTOCK-TEST-DRUG", name="Restock Test Drug")
        setup.add(drug)
        setup.flush()
        setup.add(Inventory(drug_id=drug.id, quantity_on_hand=10, low_stock_threshold=20, reorder_threshold=5))
        setup.commit()
        drug_id = drug.id
    finally:
        setup.close()

    yield Drug(id=drug_id, code="RESTOCK-TEST-DRUG", name="Restock Test Drug")

    cleanup = SessionLocal()
    try:
        cleanup.query(InventoryTransaction).filter_by(drug_id=drug_id).delete()
        cleanup.query(Inventory).filter_by(drug_id=drug_id).delete()
        cleanup.query(Drug).filter_by(id=drug_id).delete()
        cleanup.commit()
    finally:
        cleanup.close()


class TestRestock:
    def test_valid_restock_increases_stock_and_creates_ledger_entry(self, throwaway_drug: Drug):
        response = client.post(f"/api/v1/inventory/{throwaway_drug.id}/restock", json={"quantity": 50, "note": "Test delivery"})
        assert response.status_code == 200
        body = response.json()
        assert body["quantity_on_hand"] == 60

        latest_txn = body["recent_transactions"][0]
        assert latest_txn["movement_type"] == "RESTOCK"
        assert latest_txn["quantity_delta"] == 50
        assert latest_txn["quantity_before"] == 10
        assert latest_txn["quantity_after"] == 60
        assert latest_txn["note"] == "Test delivery"

    def test_zero_quantity_rejected(self, throwaway_drug: Drug):
        response = client.post(f"/api/v1/inventory/{throwaway_drug.id}/restock", json={"quantity": 0})
        assert response.status_code == 422  # Pydantic gt=0 validation

    def test_negative_quantity_rejected(self, throwaway_drug: Drug):
        response = client.post(f"/api/v1/inventory/{throwaway_drug.id}/restock", json={"quantity": -5})
        assert response.status_code == 422

    def test_restock_nonexistent_drug_returns_404(self):
        response = client.post("/api/v1/inventory/999999999/restock", json={"quantity": 10})
        assert response.status_code == 404
        assert response.json()["error"]["code"] == "DRUG_NOT_FOUND"
