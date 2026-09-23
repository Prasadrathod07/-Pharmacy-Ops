import type { StockStatus } from "./enums";

export interface DrugListItem {
  id: number;
  code: string;
  name: string;
  strength: string | null;
  dosage_form: string | null;
  is_active: boolean;
  quantity_on_hand: number;
  stock_status: StockStatus;
}

export interface DrugDetail extends DrugListItem {
  low_stock_threshold: number;
  reorder_threshold: number;
  last_restocked_at: string | null;
}
