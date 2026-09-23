import type { ListOrdersParams } from "../../api/orders";

export const dashboardKeys = {
  all: ["dashboard"] as const,
  summary: () => [...dashboardKeys.all, "summary"] as const,
  recentOrders: (params: ListOrdersParams) => [...dashboardKeys.all, "recent-orders", params] as const,
  lowStock: () => [...dashboardKeys.all, "low-stock"] as const,
};
