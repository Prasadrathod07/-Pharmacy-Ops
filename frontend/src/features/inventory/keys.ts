import type { ListInventoryParams, ListInventoryTransactionsParams } from "../../api/inventory";

export const inventoryKeys = {
  all: ["inventory"] as const,
  lists: () => [...inventoryKeys.all, "list"] as const,
  list: (params: ListInventoryParams) => [...inventoryKeys.lists(), params] as const,
  details: () => [...inventoryKeys.all, "detail"] as const,
  detail: (drugId: number) => [...inventoryKeys.details(), drugId] as const,
  transactions: (drugId: number, params: ListInventoryTransactionsParams) =>
    [...inventoryKeys.detail(drugId), "transactions", params] as const,
};
