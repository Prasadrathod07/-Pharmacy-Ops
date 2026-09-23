import logging
import secrets
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.core.database import is_transient_conflict
from app.core.exceptions import AppError
from app.domain.enums import (
    InventoryMovementSource,
    InventoryMovementType,
    OrderItemStatus,
    OrderStatus,
)
from app.domain.state_machine import InvalidTransitionError, validate_transition
from app.events.publisher import broadcaster
from app.models import Drug, Inventory, InventoryTransaction, Order, OrderItem, Patient
from app.repositories.orders import OrderRepository
from app.schemas.common import PaginatedResponse
from app.schemas.order import OrderCreateRequest, OrderDetail, OrderItemOut, OrderListItem

logger = logging.getLogger(__name__)


def _fulfilment_minutes(order: Order) -> float | None:
    if order.dispensed_at is None:
        return None
    delta = order.dispensed_at - order.created_at
    return round(delta.total_seconds() / 60, 2)


def _to_list_item(order: Order, patient_name: str, items_count: int) -> OrderListItem:
    return OrderListItem(
        id=order.id,
        order_number=order.order_number,
        patient_id=order.patient_id,
        patient_name=patient_name,
        status=order.status,
        items_count=items_count,
        created_at=order.created_at,
        dispensed_at=order.dispensed_at,
        completed_at=order.completed_at,
        fulfilment_minutes=_fulfilment_minutes(order),
    )


class OrderService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = OrderRepository(db)

    def list_orders(
        self,
        *,
        search: str | None,
        status: OrderStatus | None,
        drug_id: int | None,
        date_from: datetime | None,
        date_to: datetime | None,
        sort_by: str,
        sort_order: str,
        page_params,
    ) -> PaginatedResponse[OrderListItem]:
        rows, total = self.repo.list_orders(
            search=search,
            status=status,
            drug_id=drug_id,
            date_from=date_from,
            date_to=date_to,
            sort_by=sort_by,
            sort_order=sort_order,
            offset=page_params.offset,
            limit=page_params.page_size,
        )
        items = [_to_list_item(order, patient_name, items_count) for order, patient_name, items_count in rows]
        return PaginatedResponse.build(items, page_params.page, page_params.page_size, total)

    def get_order(self, order_id: int) -> OrderDetail:
        result = self.repo.get_order_with_details(order_id)
        if result is None:
            raise AppError("ORDER_NOT_FOUND", f"Order {order_id} not found.", status_code=404)

        order, patient_name = result
        items = [
            OrderItemOut(
                id=item.id,
                drug_id=item.drug_id,
                drug_code=item.drug.code,
                drug_name=item.drug.name,
                requested_quantity=item.requested_quantity,
                dispensed_quantity=item.dispensed_quantity,
                status=item.status,
                created_at=item.created_at,
                updated_at=item.updated_at,
            )
            for item in order.items
        ]

        return OrderDetail(
            id=order.id,
            order_number=order.order_number,
            patient_id=order.patient_id,
            patient_name=patient_name,
            status=order.status,
            items=items,
            created_at=order.created_at,
            dispensed_at=order.dispensed_at,
            completed_at=order.completed_at,
            cancelled_at=order.cancelled_at,
            updated_at=order.updated_at,
            fulfilment_minutes=_fulfilment_minutes(order),
        )

    def _get_or_create_patient(self, full_name: str) -> Patient:
        """Reuses a patient by exact trimmed-name match; otherwise creates one.

        Documented assumption (master spec §32's "Patient Behaviour" leaves
        the strategy to the implementer): simple and deterministic beats a
        fuzzy-matching heuristic for an assignment-scale system.
        """
        patient = self.db.execute(select(Patient).where(Patient.full_name == full_name)).scalar_one_or_none()
        if patient is not None:
            return patient
        patient = Patient(full_name=full_name)
        self.db.add(patient)
        self.db.flush()
        return patient

    @staticmethod
    def _generate_order_number(now: datetime) -> str:
        # Human-readable (date-prefixed) with a random suffix large enough
        # that a same-day collision is effectively impossible at this scale;
        # the DB's UNIQUE constraint on order_number remains the hard backstop.
        return f"ORD-{now.strftime('%Y%m%d')}-{secrets.token_hex(3).upper()}"

    def create_order(self, request: OrderCreateRequest) -> OrderDetail:
        drug_ids = [item.drug_id for item in request.items]

        drugs_by_id = {
            drug.id: drug
            for drug in self.db.execute(select(Drug).where(Drug.id.in_(drug_ids))).scalars().all()
        }
        missing_drug_ids = [drug_id for drug_id in drug_ids if drug_id not in drugs_by_id]
        if missing_drug_ids:
            raise AppError(
                "DRUG_NOT_FOUND",
                f"Drug(s) not found: {missing_drug_ids}",
                status_code=400,
                details={"drug_ids": missing_drug_ids},
            )

        inactive_drug_ids = [drug_id for drug_id in drug_ids if not drugs_by_id[drug_id].is_active]
        if inactive_drug_ids:
            raise AppError(
                "DRUG_INACTIVE",
                f"Drug(s) inactive: {inactive_drug_ids}",
                status_code=400,
                details={"drug_ids": inactive_drug_ids},
            )

        now = datetime.now(timezone.utc)
        created_at = request.ordered_at or now

        patient = self._get_or_create_patient(request.patient_name)

        order_number = self._generate_order_number(now)
        order = Order(
            order_number=order_number,
            patient_id=patient.id,
            status=OrderStatus.NEW,
            created_at=created_at,
        )
        self.db.add(order)
        self.db.flush()

        try:
            self._lock_and_fulfil(order, drugs_by_id, request, created_at, now)
        except OperationalError as exc:
            self.db.rollback()
            if is_transient_conflict(exc):
                logger.warning(
                    "INVENTORY_CONFLICT",
                    extra={"order_number": order_number, "drug_ids": sorted(set(drug_ids))},
                )
                raise AppError(
                    "INVENTORY_CONFLICT",
                    "Inventory changed while processing the order. Please retry.",
                    status_code=409,
                ) from exc
            raise

        self.db.commit()
        logger.info(
            "ORDER_CREATED",
            extra={"order_id": order.id, "order_number": order.order_number, "status": order.status.value},
        )
        broadcaster.publish(
            "order.created", {"order_id": order.id, "order_number": order.order_number, "status": order.status.value}
        )
        broadcaster.publish("dashboard.updated", {})

        return self.get_order(order.id)

    def _lock_and_fulfil(
        self,
        order: Order,
        drugs_by_id: dict[int, Drug],
        request: OrderCreateRequest,
        created_at: datetime,
        now: datetime,
    ) -> None:
        drug_ids = list(drugs_by_id.keys())

        # Lock every distinct inventory row this order touches, in ascending
        # drug_id order, so concurrent multi-item orders sharing drugs always
        # request locks in the same order and cannot deadlock each other
        # (master spec §16.3, §17.1).
        inventories: dict[int, Inventory] = {}
        for drug_id in sorted(set(drug_ids)):
            inventory = self.db.execute(
                select(Inventory).where(Inventory.drug_id == drug_id).with_for_update()
            ).scalar_one_or_none()
            if inventory is None:
                raise AppError(
                    "INVENTORY_NOT_FOUND",
                    f"No inventory record for drug {drug_id}.",
                    status_code=409,
                    details={"drug_id": drug_id},
                )
            inventories[drug_id] = inventory

        any_waiting = False
        all_dispensed = True

        for item_request in request.items:
            drug = drugs_by_id[item_request.drug_id]
            inventory = inventories[item_request.drug_id]

            if inventory.quantity_on_hand >= item_request.quantity:
                item = OrderItem(
                    order_id=order.id,
                    drug_id=drug.id,
                    requested_quantity=item_request.quantity,
                    dispensed_quantity=item_request.quantity,
                    status=OrderItemStatus.DISPENSED,
                    created_at=created_at,
                )
                self.db.add(item)
                self.db.flush()

                before = inventory.quantity_on_hand
                after = before - item_request.quantity
                inventory.quantity_on_hand = after

                self.db.add(
                    InventoryTransaction(
                        drug_id=drug.id,
                        order_id=order.id,
                        order_item_id=item.id,
                        movement_type=InventoryMovementType.DISPENSE,
                        source=InventoryMovementSource.NEW_ORDER,
                        quantity_delta=-item_request.quantity,
                        quantity_before=before,
                        quantity_after=after,
                        note=f"Order {order.order_number}",
                        created_at=now,
                    )
                )
                logger.info(
                    "INVENTORY_DISPENSED",
                    extra={
                        "order_id": order.id,
                        "order_number": order.order_number,
                        "drug_id": drug.id,
                        "quantity": item_request.quantity,
                    },
                )
            else:
                item = OrderItem(
                    order_id=order.id,
                    drug_id=drug.id,
                    requested_quantity=item_request.quantity,
                    dispensed_quantity=0,
                    status=OrderItemStatus.WAITING_FOR_STOCK,
                    created_at=created_at,
                )
                self.db.add(item)
                any_waiting = True
                all_dispensed = False
                logger.info(
                    "INVENTORY_SHORTAGE",
                    extra={
                        "order_id": order.id,
                        "order_number": order.order_number,
                        "drug_id": drug.id,
                        "requested": item_request.quantity,
                        "available": inventory.quantity_on_hand,
                    },
                )

        if any_waiting:
            order.status = OrderStatus.WAITING_FOR_STOCK
            logger.info(
                "ORDER_WAITING_FOR_STOCK", extra={"order_id": order.id, "order_number": order.order_number}
            )
        elif all_dispensed:
            order.status = OrderStatus.DISPENSED
            order.dispensed_at = now
            logger.info("ORDER_DISPENSED", extra={"order_id": order.id, "order_number": order.order_number})

    def complete_order(self, order_id: int) -> OrderDetail:
        order = self.db.get(Order, order_id)
        if order is None:
            raise AppError("ORDER_NOT_FOUND", f"Order {order_id} not found.", status_code=404)

        try:
            validate_transition(order.status, OrderStatus.COMPLETED)
        except InvalidTransitionError as exc:
            raise AppError("INVALID_STATE_TRANSITION", str(exc), status_code=409) from exc

        order.status = OrderStatus.COMPLETED
        order.completed_at = datetime.now(timezone.utc)
        self.db.commit()

        logger.info("ORDER_COMPLETED", extra={"order_id": order.id, "order_number": order.order_number})
        broadcaster.publish(
            "order.updated", {"order_id": order.id, "order_number": order.order_number, "status": order.status.value}
        )
        broadcaster.publish("dashboard.updated", {})
        return self.get_order(order.id)

    def cancel_order(self, order_id: int) -> OrderDetail:
        order = self.db.get(Order, order_id)
        if order is None:
            raise AppError("ORDER_NOT_FOUND", f"Order {order_id} not found.", status_code=404)

        try:
            validate_transition(order.status, OrderStatus.CANCELLED)
        except InvalidTransitionError as exc:
            raise AppError("INVALID_STATE_TRANSITION", str(exc), status_code=409) from exc

        # Documented assumption: CANCELLED is only reachable from NEW or
        # WAITING_FOR_STOCK (never from DISPENSED), so a cancelled order can
        # still contain individual items that were already DISPENSED (e.g. a
        # multi-item order where one drug was available and another wasn't).
        # Those items' stock deduction is NOT reversed here -- the medicine
        # was already allocated/handed over, and the master spec leaves
        # reversal undefined for this case. Only items still PENDING or
        # WAITING_FOR_STOCK move to CANCELLED.
        order.status = OrderStatus.CANCELLED
        order.cancelled_at = datetime.now(timezone.utc)
        for item in order.items:
            if item.status in (OrderItemStatus.PENDING, OrderItemStatus.WAITING_FOR_STOCK):
                item.status = OrderItemStatus.CANCELLED

        self.db.commit()

        logger.info("ORDER_CANCELLED", extra={"order_id": order.id, "order_number": order.order_number})
        broadcaster.publish(
            "order.updated", {"order_id": order.id, "order_number": order.order_number, "status": order.status.value}
        )
        broadcaster.publish("dashboard.updated", {})
        return self.get_order(order.id)
