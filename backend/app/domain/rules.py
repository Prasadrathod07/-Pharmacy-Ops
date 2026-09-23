"""Centralized business rules shared by services and query filters.

The single source of truth for "what stock status is this?" (master spec
§14.5-14.7). Both the Python function (used when serializing a single
Inventory row) and the SQL CASE expression (used for filtering/sorting a
list in the database) must stay in sync — they are kept side by side here.
"""
from sqlalchemy import Case, case

from app.domain.enums import StockStatus
from app.models.inventory import Inventory


def compute_stock_status(quantity_on_hand: int, low_stock_threshold: int, reorder_threshold: int) -> StockStatus:
    if quantity_on_hand == 0:
        return StockStatus.OUT_OF_STOCK
    if quantity_on_hand <= reorder_threshold:
        return StockStatus.CRITICAL
    if quantity_on_hand <= low_stock_threshold:
        return StockStatus.LOW_STOCK
    return StockStatus.HEALTHY


def stock_status_sql_case() -> Case:
    """SQL CASE mirroring compute_stock_status, for use in WHERE/ORDER BY."""
    return case(
        (Inventory.quantity_on_hand == 0, StockStatus.OUT_OF_STOCK.value),
        (Inventory.quantity_on_hand <= Inventory.reorder_threshold, StockStatus.CRITICAL.value),
        (Inventory.quantity_on_hand <= Inventory.low_stock_threshold, StockStatus.LOW_STOCK.value),
        else_=StockStatus.HEALTHY.value,
    )
