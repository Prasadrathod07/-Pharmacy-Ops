from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import PageParams, get_db, get_page_params
from app.schemas.common import PaginatedResponse
from app.schemas.drug import DrugDetail, DrugListItem
from app.services.drug_service import DrugService

router = APIRouter(prefix="/drugs", tags=["drugs"])


@router.get("", response_model=PaginatedResponse[DrugListItem], summary="Search medicines")
def list_drugs(
    search: str | None = None,
    active: bool | None = None,
    page_params: PageParams = Depends(get_page_params),
    db: Session = Depends(get_db),
) -> PaginatedResponse[DrugListItem]:
    """Searches the medicine catalogue by name or code, with live inventory
    and computed stock status attached to each result. Powers the New Order
    workspace's medicine search; the returned stock figures are informational
    only, not authoritative (see `POST /orders`).
    """
    service = DrugService(db)
    return service.list_drugs(search=search, active=active, page_params=page_params)


@router.get("/{drug_id}", response_model=DrugDetail, summary="Get a single medicine's details")
def get_drug(drug_id: int, db: Session = Depends(get_db)) -> DrugDetail:
    """Returns full drug details, current inventory, and thresholds for one medicine."""
    service = DrugService(db)
    return service.get_drug(drug_id)
