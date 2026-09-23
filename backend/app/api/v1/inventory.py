from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import PageParams, get_db, get_page_params
from app.domain.enums import InventoryMovementType, StockStatus
from app.schemas.common import PaginatedResponse
from app.schemas.inventory import InventoryDetail, InventoryListItem, InventoryTransactionOut, RestockRequest
from app.services.inventory_service import InventoryService

router = APIRouter(prefix="/inventory", tags=["inventory"])


@router.get("", response_model=PaginatedResponse[InventoryListItem], summary="List inventory with stock status")
def list_inventory(
    search: str | None = None,
    status: StockStatus | None = None,
    low_stock_only: bool = False,
    critical_only: bool = False,
    sort_by: str = Query(default="name", pattern="^(name|code|quantity_on_hand|last_restocked_at|status)$"),
    sort_order: str = Query(default="asc", pattern="^(asc|desc)$"),
    page_params: PageParams = Depends(get_page_params),
    db: Session = Depends(get_db),
) -> PaginatedResponse[InventoryListItem]:
    """Lists every drug's current stock with a computed status
    (HEALTHY / LOW_STOCK / CRITICAL / OUT_OF_STOCK). Supports search, status
    filters, sorting, and pagination for the Inventory management page.
    """
    service = InventoryService(db)
    return service.list_inventory(
        search=search,
        status=status,
        low_stock_only=low_stock_only,
        critical_only=critical_only,
        sort_by=sort_by,
        sort_order=sort_order,
        page_params=page_params,
    )


@router.get("/{drug_id}", response_model=InventoryDetail, summary="Get inventory detail and recent movements")
def get_inventory_detail(drug_id: int, db: Session = Depends(get_db)) -> InventoryDetail:
    """Returns one drug's stock, thresholds, status, and its 10 most recent
    inventory ledger movements.
    """
    service = InventoryService(db)
    return service.get_inventory_detail(drug_id)


@router.get(
    "/{drug_id}/transactions",
    response_model=PaginatedResponse[InventoryTransactionOut],
    summary="List a drug's full inventory movement ledger",
)
def list_inventory_transactions(
    drug_id: int,
    movement_type: InventoryMovementType | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    page_params: PageParams = Depends(get_page_params),
    db: Session = Depends(get_db),
) -> PaginatedResponse[InventoryTransactionOut]:
    """Paginated audit trail answering "why is this drug's stock at this
    value?" - every RESTOCK, DISPENSE, and ADJUSTMENT movement with
    quantity before/after and the related order, if any.
    """
    service = InventoryService(db)
    return service.list_transactions(
        drug_id, movement_type=movement_type, date_from=date_from, date_to=date_to, page_params=page_params
    )


@router.post("/{drug_id}/restock", response_model=InventoryDetail, summary="Restock a drug")
def restock_inventory(drug_id: int, payload: RestockRequest, db: Session = Depends(get_db)) -> InventoryDetail:
    """Increases on-hand stock by a positive quantity inside a row-locked
    transaction, records a RESTOCK ledger entry, and then automatically
    re-evaluates waiting orders for this drug in FIFO order - any that can
    now be fulfilled are dispensed immediately as part of this call.
    """
    service = InventoryService(db)
    return service.restock(drug_id, quantity=payload.quantity, note=payload.note)
