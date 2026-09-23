"""Verifies the demo seed script (app.seed) is idempotent and produces
coherent, spec-covering data. Runs against the real database directly
(not the rollback fixture) since app.seed manages its own session/commit.
"""
from app.core.database import SessionLocal
from app.models import Inventory, Order
from app.seed import DRUG_SPECS, ORDER_SPECS, run_seed


def test_seed_is_idempotent():
    first = run_seed()
    second = run_seed()

    assert first["drugs_total"] == len(DRUG_SPECS)
    assert first["orders_total"] == len(ORDER_SPECS)

    # Second run must not create anything new, regardless of what the first run did.
    assert second["drugs_created"] == 0
    assert second["orders_created"] == 0


def test_seed_covers_all_stock_statuses():
    run_seed()
    db = SessionLocal()
    try:
        statuses = set()
        for inv in db.query(Inventory).all():
            if inv.quantity_on_hand == 0:
                statuses.add("OUT_OF_STOCK")
            elif inv.quantity_on_hand <= inv.reorder_threshold:
                statuses.add("CRITICAL")
            elif inv.quantity_on_hand <= inv.low_stock_threshold:
                statuses.add("LOW_STOCK")
            else:
                statuses.add("HEALTHY")
        assert statuses == {"HEALTHY", "LOW_STOCK", "CRITICAL", "OUT_OF_STOCK"}
    finally:
        db.close()


def test_seed_includes_waiting_and_completed_orders():
    run_seed()
    db = SessionLocal()
    try:
        order_numbers = {o.order_number for o in db.query(Order).all()}
        seeded = {spec["order_number"] for spec in ORDER_SPECS}
        assert seeded.issubset(order_numbers)

        statuses = {o.status.value for o in db.query(Order).filter(Order.order_number.in_(seeded)).all()}
        assert "WAITING_FOR_STOCK" in statuses
        assert "COMPLETED" in statuses
    finally:
        db.close()
