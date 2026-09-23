import logging
from datetime import datetime, timezone

from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.core.database import is_transient_conflict
from app.core.exceptions import AppError
from app.domain.enums import InventoryMovementSource, InventoryMovementType, StockStatus
from app.domain.rules import compute_stock_status
from app.events.publisher import broadcaster
from app.models import Drug, Inventory, InventoryTransaction
from app.repositories.inventory import InventoryRepository
from app.services.fulfilment_service import process_pending_orders_for_drug
from app.schemas.common import PaginatedResponse
from app.schemas.inventory import InventoryDetail, InventoryListItem, InventoryTransactionOut

logger = logging.getLogger(__name__)


def _to_list_item(inventory: Inventory, drug: Drug) -> InventoryListItem:
    return InventoryListItem(
        drug_id=drug.id,
        drug_code=drug.code,
        drug_name=drug.name,
        strength=drug.strength,
        dosage_form=drug.dosage_form,
        quantity_on_hand=inventory.quantity_on_hand,
        low_stock_threshold=inventory.low_stock_threshold,
        reorder_threshold=inventory.reorder_threshold,
        status=compute_stock_status(
            inventory.quantity_on_hand, inventory.low_stock_threshold, inventory.reorder_threshold
        ),
        last_restocked_at=inventory.last_restocked_at,
    )


class InventoryService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = InventoryRepository(db)

    def list_inventory(
        self,
        *,
        search: str | None,
        status: StockStatus | None,
        low_stock_only: bool,
        critical_only: bool,
        sort_by: str,
        sort_order: str,
        page_params,
    ) -> PaginatedResponse[InventoryListItem]:
        rows, total = self.repo.list_inventory(
            search=search,
            status=status,
            low_stock_only=low_stock_only,
            critical_only=critical_only,
            sort_by=sort_by,
            sort_order=sort_order,
            offset=page_params.offset,
            limit=page_params.page_size,
        )
        items = [_to_list_item(inventory, drug) for inventory, drug in rows]
        return PaginatedResponse.build(items, page_params.page, page_params.page_size, total)

    def get_inventory_detail(self, drug_id: int) -> InventoryDetail:
        drug = self.db.get(Drug, drug_id)
        if drug is None:
            raise AppError("DRUG_NOT_FOUND", f"Drug {drug_id} not found.", status_code=404)

        inventory = self.repo.get_by_drug_id(drug_id)
        if inventory is None:
            raise AppError("INVENTORY_NOT_FOUND", f"No inventory record for drug {drug_id}.", status_code=404)

        recent_txns, _ = self.repo.list_transactions(
            drug_id=drug_id, movement_type=None, date_from=None, date_to=None, offset=0, limit=10
        )

        base = _to_list_item(inventory, drug)
        return InventoryDetail(
            **base.model_dump(),
            recent_transactions=[InventoryTransactionOut.model_validate(t) for t in recent_txns],
        )

    def list_transactions(
        self,
        drug_id: int,
        *,
        movement_type: InventoryMovementType | None,
        date_from: datetime | None,
        date_to: datetime | None,
        page_params,
    ) -> PaginatedResponse[InventoryTransactionOut]:
        drug = self.db.get(Drug, drug_id)
        if drug is None:
            raise AppError("DRUG_NOT_FOUND", f"Drug {drug_id} not found.", status_code=404)

        rows, total = self.repo.list_transactions(
            drug_id=drug_id,
            movement_type=movement_type,
            date_from=date_from,
            date_to=date_to,
            offset=page_params.offset,
            limit=page_params.page_size,
        )
        items = [InventoryTransactionOut.model_validate(t) for t in rows]
        return PaginatedResponse.build(items, page_params.page, page_params.page_size, total)

    def restock(self, drug_id: int, *, quantity: int, note: str | None) -> InventoryDetail:
        if quantity <= 0:
            raise AppError("INVALID_QUANTITY", "Restock quantity must be greater than zero.", status_code=400)

        drug = self.db.get(Drug, drug_id)
        if drug is None:
            raise AppError("DRUG_NOT_FOUND", f"Drug {drug_id} not found.", status_code=404)

        try:
            # Row lock: concurrent restocks/dispenses against this drug serialize
            # here rather than racing on a stale in-memory quantity (§16.3).
            inventory = self.repo.get_by_drug_id(drug_id, for_update=True)
            if inventory is None:
                raise AppError("INVENTORY_NOT_FOUND", f"No inventory record for drug {drug_id}.", status_code=404)

            before = inventory.quantity_on_hand
            after = before + quantity
            now = datetime.now(timezone.utc)

            inventory.quantity_on_hand = after
            inventory.last_restocked_at = now

            self.db.add(
                InventoryTransaction(
                    drug_id=drug_id,
                    movement_type=InventoryMovementType.RESTOCK,
                    source=InventoryMovementSource.MANUAL_RESTOCK,
                    quantity_delta=quantity,
                    quantity_before=before,
                    quantity_after=after,
                    note=note,
                    created_at=now,
                )
            )

            self.db.commit()
        except OperationalError as exc:
            self.db.rollback()
            if is_transient_conflict(exc):
                logger.warning("INVENTORY_CONFLICT", extra={"drug_id": drug_id})
                raise AppError(
                    "INVENTORY_CONFLICT",
                    "Inventory changed while processing the restock. Please retry.",
                    status_code=409,
                ) from exc
            raise

        logger.info(
            "INVENTORY_RESTOCKED",
            extra={"drug_id": drug_id, "quantity": quantity, "quantity_before": before, "quantity_after": after},
        )
        broadcaster.publish("inventory.updated", {"drug_id": drug_id})
        broadcaster.publish("dashboard.updated", {})

        # The restock above already committed, so a problem during FIFO
        # reprocessing can never undo it (master spec §15's explicit
        # requirement). process_pending_orders_for_drug swallows and logs
        # its own errors rather than raising, and publishes its own
        # order.updated/inventory.updated events for whatever it fulfils.
        process_pending_orders_for_drug(self.db, drug_id)

        return self.get_inventory_detail(drug_id)
