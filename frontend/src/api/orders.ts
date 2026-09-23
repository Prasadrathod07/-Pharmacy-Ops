import { apiRequest } from "./client";
import type { OrderCreateRequest, OrderDetail, OrderListItem, OrderStatus, PaginatedResponse } from "../types";
import { toQueryString } from "../utils/queryString";

export interface ListOrdersParams {
  search?: string;
  status?: OrderStatus;
  drug_id?: number;
  date_from?: string;
  date_to?: string;
  sort_by?: "created_at" | "order_number" | "status" | "dispensed_at" | "completed_at";
  sort_order?: "asc" | "desc";
  page?: number;
  page_size?: number;
}

export function listOrders(params: ListOrdersParams = {}) {
  return apiRequest<PaginatedResponse<OrderListItem>>(`/orders${toQueryString(params)}`);
}

export function getOrder(orderId: number) {
  return apiRequest<OrderDetail>(`/orders/${orderId}`);
}

export function createOrder(payload: OrderCreateRequest) {
  return apiRequest<OrderDetail>("/orders", { method: "POST", body: payload });
}

export function completeOrder(orderId: number) {
  return apiRequest<OrderDetail>(`/orders/${orderId}/complete`, { method: "POST" });
}

export function cancelOrder(orderId: number) {
  return apiRequest<OrderDetail>(`/orders/${orderId}/cancel`, { method: "POST" });
}
