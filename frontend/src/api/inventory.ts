import { apiRequest } from "./client";
import type {
  InventoryDetail,
  InventoryListItem,
  InventoryMovementType,
  InventoryTransaction,
  PaginatedResponse,
  RestockRequest,
  StockStatus,
} from "../types";
import { toQueryString } from "../utils/queryString";

export interface ListInventoryParams {
  search?: string;
  status?: StockStatus;
  low_stock_only?: boolean;
  critical_only?: boolean;
  sort_by?: "name" | "code" | "quantity_on_hand" | "last_restocked_at" | "status";
  sort_order?: "asc" | "desc";
  page?: number;
  page_size?: number;
}

export function listInventory(params: ListInventoryParams = {}) {
  return apiRequest<PaginatedResponse<InventoryListItem>>(`/inventory${toQueryString(params)}`);
}

export function getInventory(drugId: number) {
  return apiRequest<InventoryDetail>(`/inventory/${drugId}`);
}

export interface ListInventoryTransactionsParams {
  movement_type?: InventoryMovementType;
  date_from?: string;
  date_to?: string;
  page?: number;
  page_size?: number;
}

export function listInventoryTransactions(drugId: number, params: ListInventoryTransactionsParams = {}) {
  return apiRequest<PaginatedResponse<InventoryTransaction>>(
    `/inventory/${drugId}/transactions${toQueryString(params)}`,
  );
}

export function restockInventory(drugId: number, payload: RestockRequest) {
  return apiRequest<InventoryDetail>(`/inventory/${drugId}/restock`, {
    method: "POST",
    body: payload,
  });
}
