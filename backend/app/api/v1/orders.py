from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import PageParams, get_db, get_page_params
from app.domain.enums import OrderStatus
from app.schemas.common import PaginatedResponse
from app.schemas.order import OrderCreateRequest, OrderDetail, OrderListItem
from app.services.order_service import OrderService

router = APIRouter(prefix="/orders", tags=["orders"])


@router.get("", response_model=PaginatedResponse[OrderListItem], summary="Search and filter orders")
def list_orders(
    search: str | None = None,
    status: OrderStatus | None = None,
    drug_id: int | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    sort_by: str = Query(default="created_at", pattern="^(created_at|order_number|status|dispensed_at|completed_at)$"),
    sort_order: str = Query(default="desc", pattern="^(asc|desc)$"),
    page_params: PageParams = Depends(get_page_params),
    db: Session = Depends(get_db),
) -> PaginatedResponse[OrderListItem]:
    """Lists orders with search (order number or patient name), status/drug/
    date-range filters, sorting, and pagination. Powers the Orders page.
    """
    service = OrderService(db)
    return service.list_orders(
        search=search,
        status=status,
        drug_id=drug_id,
        date_from=date_from,
        date_to=date_to,
        sort_by=sort_by,
        sort_order=sort_order,
        page_params=page_params,
    )


@router.get("/{order_id}", response_model=OrderDetail, summary="Get order detail")
def get_order(order_id: int, db: Session = Depends(get_db)) -> OrderDetail:
    """Returns one order with its patient, line items, per-item status, and
    fulfilment time (`dispensed_at - created_at`, when dispensed).
    """
    service = OrderService(db)
    return service.get_order(order_id)


@router.post("", response_model=OrderDetail, status_code=201, summary="Create and authoritatively fulfil an order")
def create_order(payload: OrderCreateRequest, db: Session = Depends(get_db)) -> OrderDetail:
    """Creates a prescription order and evaluates it inside one atomic,
    row-locked transaction: any client-displayed stock figures are ignored
    in favor of a fresh, authoritative read. Each item is dispensed
    immediately if enough stock is available, or set to WAITING_FOR_STOCK
    otherwise; the order's overall status is derived from its items.
    """
    service = OrderService(db)
    return service.create_order(payload)


@router.post("/{order_id}/complete", response_model=OrderDetail, summary="Mark a dispensed order as completed")
def complete_order(order_id: int, db: Session = Depends(get_db)) -> OrderDetail:
    """Transitions DISPENSED -> COMPLETED. Any other current status is rejected (409)."""
    service = OrderService(db)
    return service.complete_order(order_id)


@router.post("/{order_id}/cancel", response_model=OrderDetail, summary="Cancel an order")
def cancel_order(order_id: int, db: Session = Depends(get_db)) -> OrderDetail:
    """Transitions NEW or WAITING_FOR_STOCK -> CANCELLED. Items already
    DISPENSED keep their status and stock deduction; only items still
    PENDING/WAITING_FOR_STOCK move to CANCELLED. Any other current status
    is rejected (409).
    """
    service = OrderService(db)
    return service.cancel_order(order_id)
