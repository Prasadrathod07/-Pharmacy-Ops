"""Centralized order status transition validation (master spec §11.3).

Framework-agnostic on purpose: the service layer translates a rejected
transition into the API's error contract (AppError), keeping this module
free of any FastAPI/HTTP concerns.
"""
from app.domain.enums import OrderStatus

ALLOWED_TRANSITIONS: dict[OrderStatus, frozenset[OrderStatus]] = {
    OrderStatus.NEW: frozenset({OrderStatus.WAITING_FOR_STOCK, OrderStatus.DISPENSED, OrderStatus.CANCELLED}),
    OrderStatus.WAITING_FOR_STOCK: frozenset({OrderStatus.DISPENSED, OrderStatus.CANCELLED}),
    OrderStatus.DISPENSED: frozenset({OrderStatus.COMPLETED}),
    OrderStatus.COMPLETED: frozenset(),
    OrderStatus.CANCELLED: frozenset(),
}


class InvalidTransitionError(Exception):
    def __init__(self, current: OrderStatus, target: OrderStatus):
        self.current = current
        self.target = target
        super().__init__(f"Cannot transition order from {current.value} to {target.value}.")


def validate_transition(current: OrderStatus, target: OrderStatus) -> None:
    if target not in ALLOWED_TRANSITIONS.get(current, frozenset()):
        raise InvalidTransitionError(current, target)
