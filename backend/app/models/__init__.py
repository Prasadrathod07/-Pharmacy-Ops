"""Importing this package registers all models against Base.metadata."""
from app.models.drug import Drug
from app.models.inventory import Inventory
from app.models.inventory_transaction import InventoryTransaction
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.patient import Patient

__all__ = [
    "Patient",
    "Drug",
    "Inventory",
    "Order",
    "OrderItem",
    "InventoryTransaction",
]
