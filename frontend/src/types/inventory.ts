import type { InventoryMovementSource, InventoryMovementType, StockStatus } from "./enums";

export interface InventoryListItem {
  drug_id: number;
  drug_code: string;
  drug_name: string;
  strength: string | null;
  dosage_form: string | null;
  quantity_on_hand: number;
  low_stock_threshold: number;
  reorder_threshold: number;
  status: StockStatus;
  last_restocked_at: string | null;
}

export interface InventoryTransaction {
  id: number;
  drug_id: number;
  order_id: number | null;
  order_item_id: number | null;
  movement_type: InventoryMovementType;
  source: InventoryMovementSource;
  quantity_delta: number;
  quantity_before: number;
  quantity_after: number;
  note: string | null;
  created_at: string;
}

export interface InventoryDetail extends InventoryListItem {
  recent_transactions: InventoryTransaction[];
}

export interface RestockRequest {
  quantity: number;
  note?: string | null;
}
