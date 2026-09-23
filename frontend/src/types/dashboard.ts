export interface DashboardSummary {
  orders_today: number;
  completed_today: number;
  pending_orders: number;
  average_fulfilment_minutes: number | null;
  low_stock_drugs: number;
  critical_stock_drugs: number;
}
