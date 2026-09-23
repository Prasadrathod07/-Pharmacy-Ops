"""Integration tests for the read-only order query API (master spec §32, Prompt 05).

No order-creation logic exists yet (that's Prompt 06) — these tests only
exercise listing/filtering/sorting/pagination and detail retrieval against
the seeded demo orders.
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.seed import run_seed

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def ensure_seed_data():
    run_seed()


class TestListOrders:
    def test_list_returns_seeded_orders(self):
        response = client.get("/api/v1/orders", params={"page_size": 50})
        assert response.status_code == 200
        numbers = {o["order_number"] for o in response.json()["items"]}
        assert {"ORD-SEED-0001", "ORD-SEED-0002", "ORD-SEED-0003", "ORD-SEED-0004", "ORD-SEED-0005"}.issubset(numbers)

    def test_search_by_order_number(self):
        response = client.get("/api/v1/orders", params={"search": "ORD-SEED-0001"})
        items = response.json()["items"]
        assert len(items) == 1
        assert items[0]["order_number"] == "ORD-SEED-0001"

    def test_search_by_patient_name(self):
        response = client.get("/api/v1/orders", params={"search": "Maria Garcia"})
        items = response.json()["items"]
        assert any(o["patient_name"] == "Maria Garcia" for o in items)

    def test_filter_by_status(self):
        response = client.get("/api/v1/orders", params={"status": "WAITING_FOR_STOCK", "page_size": 50})
        items = response.json()["items"]
        assert len(items) >= 2
        for item in items:
            assert item["status"] == "WAITING_FOR_STOCK"

    def test_filter_by_drug_id(self):
        drugs_response = client.get("/api/v1/drugs", params={"search": "PARACETAMOL-500-TAB"})
        drug_id = drugs_response.json()["items"][0]["id"]

        response = client.get("/api/v1/orders", params={"drug_id": drug_id, "page_size": 50})
        items = response.json()["items"]
        assert any(o["order_number"] == "ORD-SEED-0001" for o in items)

    def test_filter_by_date_range_excludes_out_of_range_orders(self):
        # ORD-SEED-0001..0005 were all created well before a far-future date_from.
        response = client.get("/api/v1/orders", params={"date_from": "2099-01-01T00:00:00Z"})
        items = response.json()["items"]
        numbers = {o["order_number"] for o in items}
        assert "ORD-SEED-0001" not in numbers

    def test_sort_by_created_at_desc_is_default(self):
        response = client.get("/api/v1/orders", params={"page_size": 50})
        timestamps = [o["created_at"] for o in response.json()["items"]]
        assert timestamps == sorted(timestamps, reverse=True)

    def test_sort_by_order_number_asc(self):
        response = client.get(
            "/api/v1/orders", params={"sort_by": "order_number", "sort_order": "asc", "page_size": 50}
        )
        numbers = [o["order_number"] for o in response.json()["items"]]
        assert numbers == sorted(numbers)

    def test_pagination(self):
        page_1 = client.get("/api/v1/orders", params={"page": 1, "page_size": 2}).json()
        page_2 = client.get("/api/v1/orders", params={"page": 2, "page_size": 2}).json()
        assert len(page_1["items"]) == 2
        ids_1 = {o["id"] for o in page_1["items"]}
        ids_2 = {o["id"] for o in page_2["items"]}
        assert ids_1.isdisjoint(ids_2)

    def test_multi_item_order_reports_correct_items_count(self):
        response = client.get("/api/v1/orders", params={"search": "ORD-SEED-0004"})
        items = response.json()["items"]
        assert items[0]["items_count"] == 2

    def test_dispensed_order_has_fulfilment_minutes_waiting_order_does_not(self):
        response = client.get("/api/v1/orders", params={"page_size": 50})
        by_number = {o["order_number"]: o for o in response.json()["items"]}
        assert by_number["ORD-SEED-0001"]["fulfilment_minutes"] is not None
        assert by_number["ORD-SEED-0003"]["fulfilment_minutes"] is None


class TestOrderDetail:
    def test_get_detail_returns_items_and_drug_metadata(self):
        list_response = client.get("/api/v1/orders", params={"search": "ORD-SEED-0004"})
        order_id = list_response.json()["items"][0]["id"]

        response = client.get(f"/api/v1/orders/{order_id}")
        assert response.status_code == 200
        body = response.json()
        assert body["order_number"] == "ORD-SEED-0004"
        assert len(body["items"]) == 2
        drug_codes = {item["drug_code"] for item in body["items"]}
        assert drug_codes == {"ATORVASTATIN-10-TAB", "METFORMIN-500-TAB"}

    def test_get_detail_for_nonexistent_order_returns_404(self):
        response = client.get("/api/v1/orders/999999999")
        assert response.status_code == 404
        assert response.json()["error"]["code"] == "ORDER_NOT_FOUND"
