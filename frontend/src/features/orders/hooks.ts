import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  cancelOrder,
  completeOrder,
  createOrder,
  getOrder,
  listOrders,
  type ListOrdersParams,
} from "../../api/orders";
import type { OrderCreateRequest } from "../../types";
import { dashboardKeys } from "../dashboard/keys";
import { inventoryKeys } from "../inventory/keys";
import { orderKeys } from "./keys";

export { orderKeys };

export function useOrders(params: ListOrdersParams = {}) {
  return useQuery({
    queryKey: orderKeys.list(params),
    queryFn: () => listOrders(params),
  });
}

export function useOrder(orderId: number | undefined) {
  return useQuery({
    queryKey: orderKeys.detail(orderId ?? -1),
    queryFn: () => getOrder(orderId as number),
    enabled: orderId !== undefined,
  });
}

function invalidateOrderAffectedQueries(queryClient: ReturnType<typeof useQueryClient>) {
  queryClient.invalidateQueries({ queryKey: orderKeys.all });
  queryClient.invalidateQueries({ queryKey: inventoryKeys.all });
  queryClient.invalidateQueries({ queryKey: dashboardKeys.all });
}

export function useCreateOrder() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: OrderCreateRequest) => createOrder(payload),
    onSuccess: () => invalidateOrderAffectedQueries(queryClient),
  });
}

export function useCompleteOrder() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (orderId: number) => completeOrder(orderId),
    onSuccess: () => invalidateOrderAffectedQueries(queryClient),
  });
}

export function useCancelOrder() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (orderId: number) => cancelOrder(orderId),
    onSuccess: () => invalidateOrderAffectedQueries(queryClient),
  });
}
