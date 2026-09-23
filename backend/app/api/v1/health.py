"""Health check endpoint."""
import logging

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import get_db

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


@router.get("/health", summary="Application and database health check")
def get_health(db: Session = Depends(get_db)) -> dict:
    """Reports application status and live database connectivity.

    Returns `{"status": "ok", "database": "connected"}` when healthy, or
    `{"status": "degraded", "database": "unavailable"}` if the database
    cannot be reached. Never exposes connection details or credentials.
    """
    try:
        db.execute(text("SELECT 1"))
        database_status = "connected"
    except Exception:
        logger.exception("health_check_database_failed")
        database_status = "unavailable"

    return {
        "status": "ok" if database_status == "connected" else "degraded",
        "database": database_status,
    }
