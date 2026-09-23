from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.domain.rules import compute_stock_status
from app.repositories.dashboard import DashboardRepository
from app.schemas.common import PaginatedResponse
from app.schemas.dashboard import DashboardSummary
from app.schemas.inventory import InventoryListItem
from app.schemas.order import OrderListItem
from app.services.order_service import OrderService


def _business_day_bounds_utc_naive(business_timezone: str, now_utc: datetime) -> tuple[datetime, datetime]:
    """[start, end) of "today" in BUSINESS_TIMEZONE, expressed as naive
    datetimes matching how timestamps are actually stored (see
    app.core.database: DATETIME columns hold naive UTC wall-clock values).
    """
    tz = ZoneInfo(business_timezone)
    now_local = now_utc.astimezone(tz)
    start_local = now_local.replace(hour=0, minute=0, second=0, microsecond=0)
    end_local = start_local + timedelta(days=1)
    start_utc = start_local.astimezone(timezone.utc).replace(tzinfo=None)
    end_utc = end_local.astimezone(timezone.utc).replace(tzinfo=None)
    return start_utc, end_utc


class DashboardService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = DashboardRepository(db)
        self.order_service = OrderService(db)

    def get_summary(self) -> DashboardSummary:
        settings = get_settings()
        now_utc = datetime.now(timezone.utc)
        start, end = _business_day_bounds_utc_naive(settings.business_timezone, now_utc)

        orders_today = self.repo.count_orders_created_between(start, end)
        completed_today = self.repo.count_orders_completed_between(start, end)
        pending_orders = self.repo.count_pending_orders()

        fulfilment_pairs = self.repo.dispensed_order_timestamps_between(start, end)
        if fulfilment_pairs:
            minutes = [(dispensed_at - created_at).total_seconds() / 60 for created_at, dispensed_at in fulfilment_pairs]
            average_fulfilment_minutes = round(sum(minutes) / len(minutes), 2)
        else:
            average_fulfilment_minutes = None

        low_stock_drugs = self.repo.count_low_stock_drugs()
        critical_stock_drugs = self.repo.count_critical_stock_drugs()

        return DashboardSummary(
            orders_today=orders_today,
            completed_today=completed_today,
            pending_orders=pending_orders,
            average_fulfilment_minutes=average_fulfilment_minutes,
            low_stock_drugs=low_stock_drugs,
            critical_stock_drugs=critical_stock_drugs,
        )

    def recent_orders(
        self,
        *,
        search: str | None,
        status,
        drug_id: int | None,
        date_from: datetime | None,
        date_to: datetime | None,
        sort_by: str,
        sort_order: str,
        page_params,
    ) -> PaginatedResponse[OrderListItem]:
        # Delegates to OrderService rather than duplicating query logic -
        # "recent orders" is the same read model as the Orders page, just
        # defaulted for a smaller dashboard panel.
        return self.order_service.list_orders(
            search=search,
            status=status,
            drug_id=drug_id,
            date_from=date_from,
            date_to=date_to,
            sort_by=sort_by,
            sort_order=sort_order,
            page_params=page_params,
        )

    def low_stock(self) -> list[InventoryListItem]:
        rows = self.repo.list_non_healthy_inventory()
        return [
            InventoryListItem(
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
            for inventory, drug in rows
        ]
