import { useNavigate, useSearchParams } from "react-router-dom";

import { DataTable, type DataTableColumn, Pagination, PageHeader, SearchInput, Select, StatusBadge } from "../components/ui";
import { useDrugs } from "../features/drugs/hooks";
import { useOrders } from "../features/orders/hooks";
import type { ListOrdersParams } from "../api/orders";
import type { OrderListItem, OrderStatus } from "../types";
import { formatDateTime, formatMinutes } from "../utils/format";

const STATUS_OPTIONS: { value: OrderStatus | ""; label: string }[] = [
  { value: "", label: "All statuses" },
  { value: "NEW", label: "New" },
  { value: "WAITING_FOR_STOCK", label: "Waiting for Stock" },
  { value: "DISPENSED", label: "Dispensed" },
  { value: "COMPLETED", label: "Completed" },
  { value: "CANCELLED", label: "Cancelled" },
];

const DEFAULT_PAGE_SIZE = 20;

export function OrdersPage() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();

  const search = searchParams.get("search") ?? "";
  const status = (searchParams.get("status") as OrderStatus | null) ?? "";
  const drugId = searchParams.get("drug_id") ?? "";
  const dateFrom = searchParams.get("date_from") ?? "";
  const dateTo = searchParams.get("date_to") ?? "";
  const sortBy = searchParams.get("sort_by") ?? "created_at";
  const sortOrder = (searchParams.get("sort_order") as "asc" | "desc" | null) ?? "desc";
  const page = Number(searchParams.get("page") ?? "1");

  const { data: drugsData } = useDrugs({ page_size: 100, active: true });

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

  const queryParams: ListOrdersParams = {
    search: search || undefined,
    status: (status || undefined) as OrderStatus | undefined,
    drug_id: drugId ? Number(drugId) : undefined,
    date_from: dateFrom || undefined,
    date_to: dateTo || undefined,
    sort_by: sortBy as ListOrdersParams["sort_by"],
    sort_order: sortOrder,
    page,
    page_size: DEFAULT_PAGE_SIZE,
  };

  const { data, isLoading, isError, refetch } = useOrders(queryParams);

  const columns: DataTableColumn<OrderListItem>[] = [
    { key: "order_number", header: "Order #", sortKey: "order_number", render: (row) => row.order_number },
    { key: "patient_name", header: "Patient", render: (row) => row.patient_name },
    { key: "items_count", header: "Items", align: "right", render: (row) => row.items_count },
    { key: "status", header: "Status", sortKey: "status", render: (row) => <StatusBadge status={row.status} /> },
    { key: "created_at", header: "Created", sortKey: "created_at", render: (row) => formatDateTime(row.created_at) },
    {
      key: "dispensed_completed",
      header: "Dispensed / Completed",
      render: (row) => formatDateTime(row.completed_at ?? row.dispensed_at),
    },
    { key: "fulfilment_minutes", header: "Fulfilment Time", align: "right", render: (row) => formatMinutes(row.fulfilment_minutes) },
  ];

  return (
    <div>
      <PageHeader title="Orders" description="Search, filter, and review prescription orders." />

      <div style={{ display: "flex", flexWrap: "wrap", gap: 10, marginBottom: 14 }}>
        <div style={{ minWidth: 220, flex: "1 1 220px" }}>
          <SearchInput
            value={search}
            onChange={(value) => updateParams({ search: value || undefined, page: undefined })}
            placeholder="Search order # or patient..."
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

        <Select
          style={{ width: 200 }}
          value={drugId}
          onChange={(event) => updateParams({ drug_id: event.target.value || undefined, page: undefined })}
        >
          <option value="">All medicines</option>
          {drugsData?.items.map((drug) => (
            <option key={drug.id} value={drug.id}>
              {drug.name} {drug.strength ?? ""}
            </option>
          ))}
        </Select>

        <input
          type="date"
          value={dateFrom}
          onChange={(event) => updateParams({ date_from: event.target.value || undefined, page: undefined })}
          aria-label="From date"
        />
        <input
          type="date"
          value={dateTo}
          onChange={(event) => updateParams({ date_to: event.target.value || undefined, page: undefined })}
          aria-label="To date"
        />
      </div>

      <DataTable
        columns={columns}
        rows={data?.items ?? []}
        rowKey={(row) => row.id}
        onRowClick={(row) => navigate(`/orders/${row.id}`)}
        isLoading={isLoading}
        isError={isError}
        onRetry={refetch}
        emptyTitle="No orders found"
        emptyDescription="Try adjusting your filters, or create a new order."
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
    </div>
  );
}
