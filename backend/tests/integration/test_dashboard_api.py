"""Integration tests for the dashboard APIs (master spec §34, §36, Prompt 09).

Uses throwaway drugs/orders with explicit `ordered_at` offsets from "now" so
assertions don't depend on exact calendar-day timing beyond "clearly today"
vs "clearly days ago" (robust against when the suite happens to run).
"""
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.main import app
from app.models import Drug, Inventory, InventoryTransaction, Order, OrderItem, Patient
from app.seed import run_seed

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def ensure_seed_data():
    run_seed()


def _make_drug(code: str, quantity_on_hand: int, low: int = 50, reorder: int = 20) -> int:
    setup = SessionLocal()
    try:
        drug = Drug(code=code, name=f"Dashboard Test {code}")
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


@pytest.fixture()
def dashboard_drug():
    drug_id = _make_drug("DASHBOARD-TEST-DRUG", quantity_on_hand=100)
    yield drug_id
    _cleanup_drug(drug_id)


class TestDashboardSummary:
    def test_summary_shape_and_types(self):
        response = client.get("/api/v1/dashboard/summary")
        assert response.status_code == 200
        body = response.json()
        for key in (
            "orders_today",
            "completed_today",
            "pending_orders",
            "average_fulfilment_minutes",
            "low_stock_drugs",
            "critical_stock_drugs",
        ):
            assert key in body
        assert isinstance(body["orders_today"], int)
        assert isinstance(body["low_stock_drugs"], int)
        assert isinstance(body["critical_stock_drugs"], int)

    def test_order_created_now_is_counted_in_orders_today(self, dashboard_drug):
        before = client.get("/api/v1/dashboard/summary").json()["orders_today"]

        client.post(
            "/api/v1/orders", json={"patient_name": "Dashboard Today Patient", "items": [{"drug_id": dashboard_drug, "quantity": 1}]}
        )

        after = client.get("/api/v1/dashboard/summary").json()["orders_today"]
        assert after == before + 1

    def test_order_created_days_ago_is_excluded_from_orders_today(self, dashboard_drug):
        before = client.get("/api/v1/dashboard/summary").json()["orders_today"]

        old_timestamp = (datetime.now(timezone.utc) - timedelta(days=3)).isoformat()
        client.post(
            "/api/v1/orders",
            json={
                "patient_name": "Dashboard Old Patient",
                "ordered_at": old_timestamp,
                "items": [{"drug_id": dashboard_drug, "quantity": 1}],
            },
        )

        after = client.get("/api/v1/dashboard/summary").json()["orders_today"]
        assert after == before  # unchanged - the old order must not count

    def test_pending_order_is_counted_in_pending_orders(self, dashboard_drug):
        # 0 stock so the item must wait.
        empty_drug = _make_drug("DASHBOARD-TEST-EMPTY", quantity_on_hand=0)
        try:
            before = client.get("/api/v1/dashboard/summary").json()["pending_orders"]

            client.post(
                "/api/v1/orders", json={"patient_name": "Dashboard Pending Patient", "items": [{"drug_id": empty_drug, "quantity": 5}]}
            )

            after = client.get("/api/v1/dashboard/summary").json()["pending_orders"]
            assert after == before + 1
        finally:
            _cleanup_drug(empty_drug)

    def test_completed_order_today_increments_completed_today(self, dashboard_drug):
        before = client.get("/api/v1/dashboard/summary").json()["completed_today"]

        create = client.post(
            "/api/v1/orders", json={"patient_name": "Dashboard Completed Patient", "items": [{"drug_id": dashboard_drug, "quantity": 1}]}
        )
        order_id = create.json()["id"]
        client.post(f"/api/v1/orders/{order_id}/complete")

        after = client.get("/api/v1/dashboard/summary").json()["completed_today"]
        assert after == before + 1

    def test_average_fulfilment_minutes_reflects_known_dispensed_order(self, dashboard_drug):
        # A fresh drug with no other orders lets us pin down the average exactly.
        solo_drug = _make_drug("DASHBOARD-TEST-SOLO", quantity_on_hand=100)
        try:
            ordered_at = datetime.now(timezone.utc) - timedelta(minutes=20)
            create = client.post(
                "/api/v1/orders",
                json={
                    "patient_name": "Dashboard Fulfilment Patient",
                    "ordered_at": ordered_at.isoformat(),
                    "items": [{"drug_id": solo_drug, "quantity": 1}],
                },
            )
            assert create.json()["status"] == "DISPENSED"

            summary = client.get("/api/v1/dashboard/summary").json()
            # dispensed_at is stamped at request time (~now), created_at was
            # backdated 20 minutes -> fulfilment ~20 minutes for at least this order.
            assert summary["average_fulfilment_minutes"] is not None
            assert summary["average_fulfilment_minutes"] > 0
        finally:
            _cleanup_drug(solo_drug)

    def test_low_and_critical_stock_counts_reflect_a_new_critical_drug(self):
        before = client.get("/api/v1/dashboard/summary").json()["critical_stock_drugs"]

        critical_drug = _make_drug("DASHBOARD-TEST-CRITICAL", quantity_on_hand=5, low=50, reorder=20)
        try:
            after = client.get("/api/v1/dashboard/summary").json()["critical_stock_drugs"]
            assert after == before + 1
        finally:
            _cleanup_drug(critical_drug)

    def test_out_of_stock_drug_counts_as_critical(self):
        before = client.get("/api/v1/dashboard/summary").json()["critical_stock_drugs"]

        oos_drug = _make_drug("DASHBOARD-TEST-OOS", quantity_on_hand=0, low=50, reorder=20)
        try:
            after = client.get("/api/v1/dashboard/summary").json()["critical_stock_drugs"]
            assert after == before + 1  # documented: OUT_OF_STOCK counts toward "critical"
        finally:
            _cleanup_drug(oos_drug)


class TestDashboardLowStock:
    def test_low_stock_list_includes_new_critical_and_low_drugs(self):
        critical_drug = _make_drug("DASHBOARD-TEST-LS-CRITICAL", quantity_on_hand=5, low=50, reorder=20)
        low_drug = _make_drug("DASHBOARD-TEST-LS-LOW", quantity_on_hand=40, low=50, reorder=20)
        healthy_drug = _make_drug("DASHBOARD-TEST-LS-HEALTHY", quantity_on_hand=500, low=50, reorder=20)
        try:
            response = client.get("/api/v1/dashboard/low-stock")
            assert response.status_code == 200
            codes = {item["drug_code"] for item in response.json()}
            assert "DASHBOARD-TEST-LS-CRITICAL" in codes
            assert "DASHBOARD-TEST-LS-LOW" in codes
            assert "DASHBOARD-TEST-LS-HEALTHY" not in codes
        finally:
            _cleanup_drug(critical_drug)
            _cleanup_drug(low_drug)
            _cleanup_drug(healthy_drug)

    def test_low_stock_list_sorted_by_quantity_ascending(self):
        response = client.get("/api/v1/dashboard/low-stock")
        quantities = [item["quantity_on_hand"] for item in response.json()]
        assert quantities == sorted(quantities)


class TestDashboardRecentOrders:
    def test_recent_orders_default_page_size_is_ten(self):
        response = client.get("/api/v1/dashboard/recent-orders")
        assert response.status_code == 200
        assert response.json()["page_size"] == 10

    def test_recent_orders_sorted_newest_first_by_default(self):
        response = client.get("/api/v1/dashboard/recent-orders", params={"page_size": 50})
        timestamps = [o["created_at"] for o in response.json()["items"]]
        assert timestamps == sorted(timestamps, reverse=True)

    def test_recent_orders_supports_status_filter(self):
        response = client.get("/api/v1/dashboard/recent-orders", params={"status": "COMPLETED", "page_size": 50})
        assert response.status_code == 200
        for item in response.json()["items"]:
            assert item["status"] == "COMPLETED"
