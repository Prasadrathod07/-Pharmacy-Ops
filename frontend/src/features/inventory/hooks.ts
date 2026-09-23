import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  getInventory,
  listInventory,
  listInventoryTransactions,
  restockInventory,
  type ListInventoryParams,
  type ListInventoryTransactionsParams,
} from "../../api/inventory";
import type { RestockRequest } from "../../types";
import { dashboardKeys } from "../dashboard/keys";
import { orderKeys } from "../orders/keys";
import { inventoryKeys } from "./keys";

export { inventoryKeys };

export function useInventoryList(params: ListInventoryParams = {}) {
  return useQuery({
    queryKey: inventoryKeys.list(params),
    queryFn: () => listInventory(params),
  });
}

export function useInventoryDetail(drugId: number | undefined) {
  return useQuery({
    queryKey: inventoryKeys.detail(drugId ?? -1),
    queryFn: () => getInventory(drugId as number),
    enabled: drugId !== undefined,
  });
}

export function useInventoryTransactions(drugId: number | undefined, params: ListInventoryTransactionsParams = {}) {
  return useQuery({
    queryKey: inventoryKeys.transactions(drugId ?? -1, params),
    queryFn: () => listInventoryTransactions(drugId as number, params),
    enabled: drugId !== undefined,
  });
}

export function useRestock(drugId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: RestockRequest) => restockInventory(drugId, payload),
    onSuccess: () => {
      // A restock can auto-fulfil waiting orders (FIFO), so orders and the
      // dashboard need refreshing too, not just inventory.
      queryClient.invalidateQueries({ queryKey: inventoryKeys.all });
      queryClient.invalidateQueries({ queryKey: orderKeys.all });
      queryClient.invalidateQueries({ queryKey: dashboardKeys.all });
    },
  });
}
