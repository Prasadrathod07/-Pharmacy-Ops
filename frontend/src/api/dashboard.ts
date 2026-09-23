import { apiRequest } from "./client";
import type { DashboardSummary, InventoryListItem, OrderListItem, PaginatedResponse } from "../types";
import type { ListOrdersParams } from "./orders";
import { toQueryString } from "../utils/queryString";

export function getDashboardSummary() {
  return apiRequest<DashboardSummary>("/dashboard/summary");
}

export function getRecentOrders(params: ListOrdersParams = {}) {
  return apiRequest<PaginatedResponse<OrderListItem>>(`/dashboard/recent-orders${toQueryString(params)}`);
}

export function getLowStock() {
  return apiRequest<InventoryListItem[]>("/dashboard/low-stock");
}
