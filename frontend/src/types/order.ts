import type { OrderItemStatus, OrderStatus } from "./enums";

export interface OrderItem {
  id: number;
  drug_id: number;
  drug_code: string;
  drug_name: string;
  requested_quantity: number;
  dispensed_quantity: number;
  status: OrderItemStatus;
  created_at: string;
  updated_at: string;
}

export interface OrderListItem {
  id: number;
  order_number: string;
  patient_id: number;
  patient_name: string;
  status: OrderStatus;
  items_count: number;
  created_at: string;
  dispensed_at: string | null;
  completed_at: string | null;
  fulfilment_minutes: number | null;
}

export interface OrderDetail {
  id: number;
  order_number: string;
  patient_id: number;
  patient_name: string;
  status: OrderStatus;
  items: OrderItem[];
  created_at: string;
  dispensed_at: string | null;
  completed_at: string | null;
  cancelled_at: string | null;
  updated_at: string;
  fulfilment_minutes: number | null;
}

export interface OrderItemCreate {
  drug_id: number;
  quantity: number;
}

export interface OrderCreateRequest {
  patient_name: string;
  ordered_at?: string;
  items: OrderItemCreate[];
}
