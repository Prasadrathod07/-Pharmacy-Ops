export type OrderStatus = "NEW" | "WAITING_FOR_STOCK" | "DISPENSED" | "COMPLETED" | "CANCELLED";

export type OrderItemStatus = "PENDING" | "WAITING_FOR_STOCK" | "DISPENSED" | "CANCELLED";

export type StockStatus = "HEALTHY" | "LOW_STOCK" | "CRITICAL" | "OUT_OF_STOCK";

export type InventoryMovementType = "RESTOCK" | "DISPENSE" | "ADJUSTMENT";

export type InventoryMovementSource =
  | "NEW_ORDER"
  | "PENDING_FULFILMENT"
  | "MANUAL_RESTOCK"
  | "MANUAL_ADJUSTMENT";
