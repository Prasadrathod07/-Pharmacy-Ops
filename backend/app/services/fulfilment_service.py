"""FIFO pending-order fulfilment after a restock (master spec §15).

Deliberately runs as its own transaction, separate from the restock that
triggers it (see app.services.inventory_service.InventoryService.restock).
The restock has already committed by the time this runs, so a problem here
can never roll back an already-successful restock — it is caught, logged,
and swallowed rather than propagated (master spec §15's explicit "Restock
itself must remain successful even if post-restock processing encounters a
recoverable problem").
"""
import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.enums import InventoryMovementSource, InventoryMovementType, OrderItemStatus, OrderStatus
from app.events.publisher import broadcaster
from app.models import Inventory, InventoryTransaction, Order, OrderItem

logger = logging.getLogger(__name__)


def process_pending_orders_for_drug(db: Session, drug_id: int) -> int:
    """Fulfils WAITING_FOR_STOCK items for `drug_id`, oldest order first,
    stopping as soon as the next item in line can't be fully covered by the
    remaining stock (strict FIFO — never skips ahead to a later, smaller item;
    master spec §15). Returns the number of items fulfilled.
    """
    try:
        return _run(db, drug_id)
    except Exception:
        db.rollback()
        logger.exception("PENDING_FULFILMENT_FAILED", extra={"drug_id": drug_id})
        return 0


def _run(db: Session, drug_id: int) -> int:
    inventory = db.execute(
        select(Inventory).where(Inventory.drug_id == drug_id).with_for_update()
    ).scalar_one_or_none()
    if inventory is None:
        return 0

    waiting_rows = db.execute(
        select(OrderItem, Order)
        .join(Order, OrderItem.order_id == Order.id)
        .where(OrderItem.drug_id == drug_id, OrderItem.status == OrderItemStatus.WAITING_FOR_STOCK)
        .order_by(Order.created_at.asc(), OrderItem.id.asc())
    ).all()

    now = datetime.now(timezone.utc)
    fulfilled_count = 0
    affected_orders: dict[int, dict] = {}

    for item, order in waiting_rows:
        if inventory.quantity_on_hand < item.requested_quantity:
            break  # strict FIFO: stop here, do not skip ahead to a smaller later item

        before = inventory.quantity_on_hand
        after = before - item.requested_quantity
        inventory.quantity_on_hand = after

        item.dispensed_quantity = item.requested_quantity
        item.status = OrderItemStatus.DISPENSED

        db.add(
            InventoryTransaction(
                drug_id=drug_id,
                order_id=order.id,
                order_item_id=item.id,
                movement_type=InventoryMovementType.DISPENSE,
                source=InventoryMovementSource.PENDING_FULFILMENT,
                quantity_delta=-item.requested_quantity,
                quantity_before=before,
                quantity_after=after,
                note=f"Auto-fulfilled after restock (order {order.order_number})",
                created_at=now,
            )
        )

        logger.info(
            "PENDING_ORDER_FULFILLED",
            extra={
                "order_id": order.id,
                "order_number": order.order_number,
                "drug_id": drug_id,
                "quantity": item.requested_quantity,
            },
        )

        _recompute_order_status(db, order, now)
        fulfilled_count += 1
        affected_orders[order.id] = {"order_id": order.id, "order_number": order.order_number, "status": order.status.value}

    db.commit()

    for payload in affected_orders.values():
        broadcaster.publish("order.updated", payload)
    if fulfilled_count > 0:
        broadcaster.publish("inventory.updated", {"drug_id": drug_id})
        broadcaster.publish("dashboard.updated", {})

    return fulfilled_count


def _recompute_order_status(db: Session, order: Order, now: datetime) -> None:
    items = db.execute(select(OrderItem).where(OrderItem.order_id == order.id)).scalars().all()

    if any(item.status == OrderItemStatus.WAITING_FOR_STOCK for item in items):
        return  # still blocked by at least one other item; order stays WAITING_FOR_STOCK

    if all(item.status == OrderItemStatus.DISPENSED for item in items):
        order.status = OrderStatus.DISPENSED
        order.dispensed_at = now
        logger.info("ORDER_DISPENSED", extra={"order_id": order.id, "order_number": order.order_number})
