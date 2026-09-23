from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import PageParams, get_db
from app.domain.enums import OrderStatus
from app.schemas.common import PaginatedResponse
from app.schemas.dashboard import DashboardSummary
from app.schemas.inventory import InventoryListItem
from app.schemas.order import OrderListItem
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummary, summary="Manager dashboard KPI summary")
def get_dashboard_summary(db: Session = Depends(get_db)) -> DashboardSummary:
    """Orders today, completed today, pending count, average fulfilment
    time, and low/critical stock counts - all computed for the business day
    in `BUSINESS_TIMEZONE`, not naive UTC midnight.
    """
    service = DashboardService(db)
    return service.get_summary()


@router.get("/recent-orders", response_model=PaginatedResponse[OrderListItem], summary="Recent orders for the dashboard")
def get_recent_orders(
    search: str | None = None,
    status: OrderStatus | None = None,
    drug_id: int | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    sort_by: str = Query(default="created_at", pattern="^(created_at|order_number|status|dispensed_at|completed_at)$"),
    sort_order: str = Query(default="desc", pattern="^(asc|desc)$"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
) -> PaginatedResponse[OrderListItem]:
    """Same filtering/sorting as `GET /orders`, defaulted to a smaller page
    size for a dashboard panel rather than the full Orders page.
    """
    service = DashboardService(db)
    return service.recent_orders(
        search=search,
        status=status,
        drug_id=drug_id,
        date_from=date_from,
        date_to=date_to,
        sort_by=sort_by,
        sort_order=sort_order,
        page_params=PageParams(page=page, page_size=page_size),
    )


@router.get("/low-stock", response_model=list[InventoryListItem], summary="Drugs needing attention")
def get_low_stock(db: Session = Depends(get_db)) -> list[InventoryListItem]:
    """Every drug whose computed status is not HEALTHY (LOW_STOCK, CRITICAL,
    or OUT_OF_STOCK), sorted by quantity ascending - most urgent first.
    """
    service = DashboardService(db)
    return service.low_stock()
