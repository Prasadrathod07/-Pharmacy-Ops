"""Integration tests for the drug search API (master spec §31, Prompt 05)."""
import pytest
from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.main import app
from app.models import Drug
from app.seed import run_seed

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def ensure_seed_data():
    run_seed()


class TestListDrugs:
    def test_list_returns_seeded_drugs_with_inventory(self):
        response = client.get("/api/v1/drugs", params={"page_size": 50})
        assert response.status_code == 200
        body = response.json()
        paracetamol = next(d for d in body["items"] if d["code"] == "PARACETAMOL-500-TAB")
        assert paracetamol["quantity_on_hand"] == 500
        assert paracetamol["stock_status"] == "HEALTHY"

    def test_search_by_name(self):
        response = client.get("/api/v1/drugs", params={"search": "amoxicillin"})
        items = response.json()["items"]
        assert len(items) == 1
        assert items[0]["code"] == "AMOXICILLIN-500-CAP"

    def test_search_by_code(self):
        response = client.get("/api/v1/drugs", params={"search": "OMEPRAZOLE-20-CAP"})
        items = response.json()["items"]
        assert len(items) == 1

    def test_pagination(self):
        page_1 = client.get("/api/v1/drugs", params={"page": 1, "page_size": 4}).json()
        page_2 = client.get("/api/v1/drugs", params={"page": 2, "page_size": 4}).json()
        assert len(page_1["items"]) == 4
        ids_1 = {d["id"] for d in page_1["items"]}
        ids_2 = {d["id"] for d in page_2["items"]}
        assert ids_1.isdisjoint(ids_2)


@pytest.fixture()
def inactive_drug():
    setup = SessionLocal()
    try:
        drug = Drug(code="INACTIVE-TEST-DRUG", name="Inactive Test Drug", is_active=False)
        setup.add(drug)
        setup.commit()
        drug_id = drug.id
    finally:
        setup.close()

    yield drug_id

    cleanup = SessionLocal()
    try:
        cleanup.query(Drug).filter_by(id=drug_id).delete()
        cleanup.commit()
    finally:
        cleanup.close()


class TestActiveFilter:
    def test_active_true_excludes_inactive_drug(self, inactive_drug):
        response = client.get("/api/v1/drugs", params={"active": True, "page_size": 50})
        ids = {d["id"] for d in response.json()["items"]}
        assert inactive_drug not in ids

    def test_active_false_returns_only_inactive(self, inactive_drug):
        response = client.get("/api/v1/drugs", params={"active": False, "page_size": 50})
        ids = {d["id"] for d in response.json()["items"]}
        assert inactive_drug in ids

    def test_no_active_filter_returns_both(self, inactive_drug):
        response = client.get("/api/v1/drugs", params={"page_size": 50})
        ids = {d["id"] for d in response.json()["items"]}
        assert inactive_drug in ids


class TestDrugDetail:
    def test_get_detail_for_seeded_drug(self):
        list_response = client.get("/api/v1/drugs", params={"search": "PARACETAMOL-500-TAB"})
        drug_id = list_response.json()["items"][0]["id"]

        response = client.get(f"/api/v1/drugs/{drug_id}")
        assert response.status_code == 200
        body = response.json()
        assert body["code"] == "PARACETAMOL-500-TAB"
        assert body["low_stock_threshold"] == 50

    def test_get_detail_for_nonexistent_drug_returns_404(self):
        response = client.get("/api/v1/drugs/999999999")
        assert response.status_code == 404
        assert response.json()["error"]["code"] == "DRUG_NOT_FOUND"
