import { useQuery } from "@tanstack/react-query";

import { getDashboardSummary, getLowStock, getRecentOrders } from "../../api/dashboard";
import type { ListOrdersParams } from "../../api/orders";
import { dashboardKeys } from "./keys";

export { dashboardKeys };

export function useDashboardSummary() {
  return useQuery({
    queryKey: dashboardKeys.summary(),
    queryFn: getDashboardSummary,
  });
}

export function useRecentOrders(params: ListOrdersParams = {}) {
  return useQuery({
    queryKey: dashboardKeys.recentOrders(params),
    queryFn: () => getRecentOrders(params),
  });
}

export function useLowStock() {
  return useQuery({
    queryKey: dashboardKeys.lowStock(),
    queryFn: getLowStock,
  });
}
