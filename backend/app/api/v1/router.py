"""Aggregates all v1 API routers. Feature routers are added as they are implemented."""
from fastapi import APIRouter

from app.api.v1 import dashboard, drugs, events, health, inventory, orders

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health.router)
api_router.include_router(drugs.router)
api_router.include_router(inventory.router)
api_router.include_router(orders.router)
api_router.include_router(dashboard.router)
api_router.include_router(events.router)
