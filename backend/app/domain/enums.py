"""Centralized domain enums. See master spec §11, §12, §18.2."""
import enum


class OrderStatus(str, enum.Enum):
    NEW = "NEW"
    WAITING_FOR_STOCK = "WAITING_FOR_STOCK"
    DISPENSED = "DISPENSED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class OrderItemStatus(str, enum.Enum):
    PENDING = "PENDING"
    WAITING_FOR_STOCK = "WAITING_FOR_STOCK"
    DISPENSED = "DISPENSED"
    CANCELLED = "CANCELLED"


class InventoryMovementType(str, enum.Enum):
    RESTOCK = "RESTOCK"
    DISPENSE = "DISPENSE"
    ADJUSTMENT = "ADJUSTMENT"


class InventoryMovementSource(str, enum.Enum):
    NEW_ORDER = "NEW_ORDER"
    PENDING_FULFILMENT = "PENDING_FULFILMENT"
    MANUAL_RESTOCK = "MANUAL_RESTOCK"
    MANUAL_ADJUSTMENT = "MANUAL_ADJUSTMENT"


class StockStatus(str, enum.Enum):
    """Computed, not persisted. See app.domain.rules.compute_stock_status."""

    HEALTHY = "HEALTHY"
    LOW_STOCK = "LOW_STOCK"
    CRITICAL = "CRITICAL"
    OUT_OF_STOCK = "OUT_OF_STOCK"
