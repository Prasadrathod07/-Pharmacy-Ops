"""Deterministic, idempotent demo/dev seed data.

Run from `backend/` with the virtualenv active:

    python -m app.seed

Re-running is safe: drugs are matched by their unique `code`, patients by
`full_name`, and orders by `order_number`. Anything that already exists is
left untouched and its associated inventory/ledger effects are not reapplied.

This writes directly through the ORM rather than the (not-yet-implemented)
order/inventory services, since it exists to populate demo data, not to
exercise the authoritative fulfilment path built in later prompts.
"""
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.logging import configure_logging
from app.domain.enums import (
    InventoryMovementSource,
    InventoryMovementType,
    OrderItemStatus,
    OrderStatus,
)
from app.models import Drug, Inventory, InventoryTransaction, Order, OrderItem, Patient

logger = logging.getLogger(__name__)

# code -> (name, strength, dosage_form, low_stock_threshold, reorder_threshold, baseline_restock_qty)
# baseline_restock_qty is the initial delivery quantity; some of it is later
# consumed by seeded orders below so the final on-hand quantity lands on the
# intended demo stock status (HEALTHY / LOW_STOCK / CRITICAL / OUT_OF_STOCK).
DRUG_SPECS = [
    dict(code="PARACETAMOL-500-TAB", name="Paracetamol", strength="500 mg", dosage_form="Tablet", low=50, reorder=20, baseline=510),
    dict(code="AMOXICILLIN-500-CAP", name="Amoxicillin", strength="500 mg", dosage_form="Capsule", low=50, reorder=20, baseline=40),
    dict(code="AZITHROMYCIN-250-TAB", name="Azithromycin", strength="250 mg", dosage_form="Tablet", low=50, reorder=10, baseline=8),
    dict(code="METFORMIN-500-TAB", name="Metformin", strength="500 mg", dosage_form="Tablet", low=50, reorder=20, baseline=15, deplete_after_restock=True),
    dict(code="ATORVASTATIN-10-TAB", name="Atorvastatin", strength="10 mg", dosage_form="Tablet", low=40, reorder=15, baseline=320),
    dict(code="CETIRIZINE-10-TAB", name="Cetirizine", strength="10 mg", dosage_form="Tablet", low=30, reorder=10, baseline=255),
    dict(code="VITAMIND3-1000IU-CAP", name="Vitamin D3", strength="1000 IU", dosage_form="Capsule", low=30, reorder=10, baseline=25),
    dict(code="OMEPRAZOLE-20-CAP", name="Omeprazole", strength="20 mg", dosage_form="Capsule", low=40, reorder=10, baseline=8),
]

# Representative orders demonstrating every lifecycle state from master spec §11.
# offsets are minutes-ago from "now" (seed run time), oldest first.
ORDER_SPECS = [
    dict(
        order_number="ORD-SEED-0001",
        patient_name="Maria Garcia",
        created_minutes_ago=240,
        dispensed_minutes_ago=230,
        completed_minutes_ago=210,
        items=[("PARACETAMOL-500-TAB", 10)],
    ),
    dict(
        order_number="ORD-SEED-0002",
        patient_name="John Doe",
        created_minutes_ago=180,
        dispensed_minutes_ago=175,
        completed_minutes_ago=None,
        items=[("CETIRIZINE-10-TAB", 5)],
    ),
    dict(
        order_number="ORD-SEED-0003",
        patient_name="Wei Chen",
        created_minutes_ago=30,
        dispensed_minutes_ago=None,
        completed_minutes_ago=None,
        items=[("AMOXICILLIN-500-CAP", 100)],  # exceeds the 40 on-hand -> waiting
    ),
    dict(
        order_number="ORD-SEED-0004",
        patient_name="Priya Sharma",
        created_minutes_ago=1440,  # ~1 day ago
        dispensed_minutes_ago=None,
        completed_minutes_ago=None,
        items=[
            ("ATORVASTATIN-10-TAB", 20),  # sufficient -> dispensed
            ("METFORMIN-500-TAB", 10),  # out of stock -> waiting
        ],
    ),
    dict(
        order_number="ORD-SEED-0005",
        patient_name="Alex Johnson",
        created_minutes_ago=300,
        dispensed_minutes_ago=285,
        completed_minutes_ago=180,
        items=[("OMEPRAZOLE-20-CAP", 3)],
    ),
]


def _get_or_create_drug(db: Session, spec: dict) -> tuple[Drug, bool]:
    drug = db.query(Drug).filter_by(code=spec["code"]).one_or_none()
    if drug is not None:
        return drug, False
    drug = Drug(code=spec["code"], name=spec["name"], strength=spec["strength"], dosage_form=spec["dosage_form"])
    db.add(drug)
    db.flush()
    return drug, True


def _ensure_inventory(db: Session, drug: Drug, spec: dict) -> Inventory:
    inventory = db.query(Inventory).filter_by(drug_id=drug.id).one_or_none()
    if inventory is not None:
        return inventory
    inventory = Inventory(
        drug_id=drug.id, quantity_on_hand=0, low_stock_threshold=spec["low"], reorder_threshold=spec["reorder"]
    )
    db.add(inventory)
    db.flush()
    return inventory


def _record_movement(
    db: Session,
    *,
    drug: Drug,
    inventory: Inventory,
    delta: int,
    movement_type: InventoryMovementType,
    source: InventoryMovementSource,
    note: str,
    order: Order | None = None,
    order_item: OrderItem | None = None,
    occurred_at: datetime,
) -> None:
    before = inventory.quantity_on_hand
    after = before + delta
    inventory.quantity_on_hand = after
    if movement_type == InventoryMovementType.RESTOCK:
        inventory.last_restocked_at = occurred_at

    db.add(
        InventoryTransaction(
            drug_id=drug.id,
            order_id=order.id if order else None,
            order_item_id=order_item.id if order_item else None,
            movement_type=movement_type,
            source=source,
            quantity_delta=delta,
            quantity_before=before,
            quantity_after=after,
            note=note,
            created_at=occurred_at,
        )
    )
    db.flush()


def _get_or_create_patient(db: Session, full_name: str) -> Patient:
    patient = db.query(Patient).filter_by(full_name=full_name).one_or_none()
    if patient is not None:
        return patient
    patient = Patient(full_name=full_name)
    db.add(patient)
    db.flush()
    return patient


def _seed_drugs_and_inventory(db: Session, now: datetime) -> tuple[dict[str, Drug], int]:
    drugs: dict[str, Drug] = {}
    created_count = 0

    for spec in DRUG_SPECS:
        drug, created = _get_or_create_drug(db, spec)
        inventory = _ensure_inventory(db, drug, spec)
        drugs[spec["code"]] = drug

        if created:
            created_count += 1
            _record_movement(
                db,
                drug=drug,
                inventory=inventory,
                delta=spec["baseline"],
                movement_type=InventoryMovementType.RESTOCK,
                source=InventoryMovementSource.MANUAL_RESTOCK,
                note="Initial seed stock delivery",
                occurred_at=now - timedelta(days=2),
            )
            if spec.get("deplete_after_restock"):
                _record_movement(
                    db,
                    drug=drug,
                    inventory=inventory,
                    delta=-spec["baseline"],
                    movement_type=InventoryMovementType.ADJUSTMENT,
                    source=InventoryMovementSource.MANUAL_ADJUSTMENT,
                    note="Seed: stock correction after physical count",
                    occurred_at=now - timedelta(days=1),
                )

    return drugs, created_count


def _seed_orders(db: Session, drugs: dict[str, Drug], now: datetime) -> int:
    created_count = 0

    for spec in ORDER_SPECS:
        existing = db.query(Order).filter_by(order_number=spec["order_number"]).one_or_none()
        if existing is not None:
            continue

        patient = _get_or_create_patient(db, spec["patient_name"])
        created_at = now - timedelta(minutes=spec["created_minutes_ago"])

        order = Order(
            order_number=spec["order_number"],
            patient_id=patient.id,
            status=OrderStatus.NEW,
            created_at=created_at,
        )
        db.add(order)
        db.flush()

        any_waiting = False
        all_dispensed = True

        for drug_code, quantity in spec["items"]:
            drug = drugs[drug_code]
            inventory = db.query(Inventory).filter_by(drug_id=drug.id).one()

            if inventory.quantity_on_hand >= quantity:
                item = OrderItem(
                    order_id=order.id,
                    drug_id=drug.id,
                    requested_quantity=quantity,
                    dispensed_quantity=quantity,
                    status=OrderItemStatus.DISPENSED,
                    created_at=created_at,
                )
                db.add(item)
                db.flush()
                _record_movement(
                    db,
                    drug=drug,
                    inventory=inventory,
                    delta=-quantity,
                    movement_type=InventoryMovementType.DISPENSE,
                    source=InventoryMovementSource.NEW_ORDER,
                    note=f"Seed order {spec['order_number']}",
                    order=order,
                    order_item=item,
                    occurred_at=created_at,
                )
            else:
                item = OrderItem(
                    order_id=order.id,
                    drug_id=drug.id,
                    requested_quantity=quantity,
                    dispensed_quantity=0,
                    status=OrderItemStatus.WAITING_FOR_STOCK,
                    created_at=created_at,
                )
                db.add(item)
                db.flush()
                any_waiting = True
                all_dispensed = False

        if any_waiting:
            order.status = OrderStatus.WAITING_FOR_STOCK
        elif all_dispensed:
            dispensed_at = now - timedelta(minutes=spec["dispensed_minutes_ago"])
            order.status = OrderStatus.DISPENSED
            order.dispensed_at = dispensed_at

            if spec["completed_minutes_ago"] is not None:
                order.status = OrderStatus.COMPLETED
                order.completed_at = now - timedelta(minutes=spec["completed_minutes_ago"])

        db.flush()
        created_count += 1

    return created_count


def run_seed() -> dict[str, int]:
    db = SessionLocal()
    now = datetime.now(timezone.utc)
    try:
        drugs, drugs_created = _seed_drugs_and_inventory(db, now)
        orders_created = _seed_orders(db, drugs, now)
        db.commit()

        summary = {
            "drugs_created": drugs_created,
            "drugs_total": len(DRUG_SPECS),
            "orders_created": orders_created,
            "orders_total": len(ORDER_SPECS),
        }
        logger.info("seed_completed", extra=summary)
        return summary
    except Exception:
        db.rollback()
        logger.exception("seed_failed")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    configure_logging()
    run_seed()
