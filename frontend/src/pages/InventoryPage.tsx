import { useState } from "react";
import { useSearchParams } from "react-router-dom";

import { Button, DataTable, type DataTableColumn, PageHeader, Pagination, SearchInput, Select, StatusBadge } from "../components/ui";
import { InventoryDetailModal } from "../features/inventory/components/InventoryDetailModal";
import { RestockModal } from "../features/inventory/components/RestockModal";
import { useInventoryList } from "../features/inventory/hooks";
import type { ListInventoryParams } from "../api/inventory";
import type { InventoryListItem, StockStatus } from "../types";
import { formatDateTime } from "../utils/format";

const STATUS_OPTIONS: { value: StockStatus | ""; label: string }[] = [
  { value: "", label: "All statuses" },
  { value: "HEALTHY", label: "Healthy" },
  { value: "LOW_STOCK", label: "Low Stock" },
  { value: "CRITICAL", label: "Critical" },
  { value: "OUT_OF_STOCK", label: "Out of Stock" },
];

const DEFAULT_PAGE_SIZE = 20;

export function InventoryPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [restockTarget, setRestockTarget] = useState<InventoryListItem | null>(null);
  const [detailTarget, setDetailTarget] = useState<InventoryListItem | null>(null);

  const search = searchParams.get("search") ?? "";
  const status = (searchParams.get("status") as StockStatus | null) ?? "";
  const sortBy = searchParams.get("sort_by") ?? "name";
  const sortOrder = (searchParams.get("sort_order") as "asc" | "desc" | null) ?? "asc";
  const page = Number(searchParams.get("page") ?? "1");

  function updateParams(patch: Record<string, string | undefined>) {
    const next = new URLSearchParams(searchParams);
    for (const [key, value] of Object.entries(patch)) {
      if (value === undefined || value === "") {
        next.delete(key);
      } else {
        next.set(key, value);
      }
    }
    setSearchParams(next);
  }

  const queryParams: ListInventoryParams = {
    search: search || undefined,
    status: (status || undefined) as StockStatus | undefined,
    sort_by: sortBy as ListInventoryParams["sort_by"],
    sort_order: sortOrder,
    page,
    page_size: DEFAULT_PAGE_SIZE,
  };

  const { data, isLoading, isError, refetch } = useInventoryList(queryParams);

  const columns: DataTableColumn<InventoryListItem>[] = [
    { key: "name", header: "Drug", sortKey: "name", render: (row) => `${row.drug_name} ${row.strength ?? ""}` },
    { key: "code", header: "Code", sortKey: "code", render: (row) => row.drug_code },
    { key: "quantity", header: "Current Stock", align: "right", sortKey: "quantity_on_hand", render: (row) => row.quantity_on_hand },
    { key: "low_threshold", header: "Low Threshold", align: "right", render: (row) => row.low_stock_threshold },
    { key: "reorder_threshold", header: "Reorder Threshold", align: "right", render: (row) => row.reorder_threshold },
    { key: "status", header: "Status", sortKey: "status", render: (row) => <StatusBadge status={row.status} /> },
    { key: "last_restocked", header: "Last Restocked", sortKey: "last_restocked_at", render: (row) => formatDateTime(row.last_restocked_at) },
    {
      key: "actions",
      header: "Actions",
      render: (row) => (
        <div style={{ display: "flex", gap: 6 }}>
          <Button variant="secondary" size="sm" onClick={() => setDetailTarget(row)}>
            View
          </Button>
          <Button size="sm" onClick={() => setRestockTarget(row)}>
            Restock
          </Button>
        </div>
      ),
    },
  ];

  return (
    <div>
      <PageHeader title="Inventory" description="Stock levels, thresholds, and restocking." />

      <div style={{ display: "flex", flexWrap: "wrap", gap: 10, marginBottom: 14 }}>
        <div style={{ minWidth: 240, flex: "1 1 240px" }}>
          <SearchInput
            value={search}
            onChange={(value) => updateParams({ search: value || undefined, page: undefined })}
            placeholder="Search by name or code..."
          />
        </div>

        <Select
          style={{ width: 190 }}
          value={status}
          onChange={(event) => updateParams({ status: event.target.value || undefined, page: undefined })}
        >
          {STATUS_OPTIONS.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </Select>
      </div>

      <DataTable
        columns={columns}
        rows={data?.items ?? []}
        rowKey={(row) => row.drug_id}
        isLoading={isLoading}
        isError={isError}
        onRetry={refetch}
        emptyTitle="No drugs found"
        emptyDescription="Try adjusting your search or status filter."
        sort={{
          sortBy,
          sortOrder,
          onSortChange: (nextSortBy) => {
            const nextOrder = sortBy === nextSortBy && sortOrder === "asc" ? "desc" : "asc";
            updateParams({ sort_by: nextSortBy, sort_order: nextOrder, page: undefined });
          },
        }}
      />

      {data ? (
        <Pagination
          page={data.page}
          pageSize={data.page_size}
          total={data.total}
          totalPages={data.total_pages}
          onPageChange={(nextPage) => updateParams({ page: String(nextPage) })}
        />
      ) : null}

      {restockTarget ? <RestockModal item={restockTarget} onClose={() => setRestockTarget(null)} /> : null}
      {detailTarget ? (
        <InventoryDetailModal drugId={detailTarget.drug_id} drugName={detailTarget.drug_name} onClose={() => setDetailTarget(null)} />
      ) : null}
    </div>
  );
}
