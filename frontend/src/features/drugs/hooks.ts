import { useQuery } from "@tanstack/react-query";

import { getDrug, listDrugs, type ListDrugsParams } from "../../api/drugs";

export const drugKeys = {
  all: ["drugs"] as const,
  lists: () => [...drugKeys.all, "list"] as const,
  list: (params: ListDrugsParams) => [...drugKeys.lists(), params] as const,
  details: () => [...drugKeys.all, "detail"] as const,
  detail: (id: number) => [...drugKeys.details(), id] as const,
};

export function useDrugs(params: ListDrugsParams = {}) {
  return useQuery({
    queryKey: drugKeys.list(params),
    queryFn: () => listDrugs(params),
  });
}

export function useDrug(drugId: number | undefined) {
  return useQuery({
    queryKey: drugKeys.detail(drugId ?? -1),
    queryFn: () => getDrug(drugId as number),
    enabled: drugId !== undefined,
  });
}
