import { apiRequest } from "./client";
import type { DrugDetail, DrugListItem, PaginatedResponse } from "../types";
import { toQueryString } from "../utils/queryString";

export interface ListDrugsParams {
  search?: string;
  active?: boolean;
  page?: number;
  page_size?: number;
}

export function listDrugs(params: ListDrugsParams = {}) {
  return apiRequest<PaginatedResponse<DrugListItem>>(`/drugs${toQueryString(params)}`);
}

export function getDrug(drugId: number) {
  return apiRequest<DrugDetail>(`/drugs/${drugId}`);
}
