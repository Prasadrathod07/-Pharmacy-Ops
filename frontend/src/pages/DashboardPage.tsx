import { useNavigate } from "react-router-dom";

import { ErrorState } from "../components/feedback";
import { DataTable, type DataTableColumn, KpiCard, PageHeader, StatusBadge } from "../components/ui";
import { useDashboardSummary, useLowStock, useRecentOrders } from "../features/dashboard/hooks";
import type { InventoryListItem, OrderListItem } from "../types";
import { formatDateTime, formatDurationSince, formatMinutes } from "../utils/format";
import styles from "./DashboardPage.module.css";

export function DashboardPage() {
  const navigate = useNavigate();
  const {
    data: summary,
    isLoading: summaryLoading,
    isError: summaryError,
    refetch: refetchSummary,
  } = useDashboardSummary();
  const { data: recentOrders, isLoading: recentLoading, isError: recentError, refetch: refetchRecent } = useRecentOrders({
    page_size: 8,
  });
  const { data: lowStock, isLoading: lowStockLoading, isError: lowStockError, refetch: refetchLowStock } = useLowStock();
  const {
    data: pendingOrders,
    isLoading: pendingLoading,
    isError: pendingError,
    refetch: refetchPending,
  } = useRecentOrders({ status: "WAITING_FOR_STOCK", sort_by: "created_at", sort_order: "asc", page_size: 6 });

  const recentColumns: DataTableColumn<OrderListItem>[] = [
    { key: "order_number", header: "Order #", render: (row) => row.order_number },
    { key: "patient_name", header: "Patient", render: (row) => row.patient_name },
    { key: "status", header: "Status", render: (row) => <StatusBadge status={row.status} /> },
    { key: "created_at", header: "Created", render: (row) => formatDateTime(row.created_at) },
    { key: "fulfilment_minutes", header: "Fulfilment", align: "right", render: (row) => formatMinutes(row.fulfilment_minutes) },
  ];

  const lowStockColumns: DataTableColumn<InventoryListItem>[] = [
    { key: "drug", header: "Drug", render: (row) => row.drug_name },
    { key: "quantity", header: "Stock", align: "right", render: (row) => row.quantity_on_hand },
    { key: "status", header: "Status", render: (row) => <StatusBadge status={row.status} /> },
  ];

  const pendingColumns: DataTableColumn<OrderListItem>[] = [
    { key: "order_number", header: "Order #", render: (row) => row.order_number },
    { key: "patient_name", header: "Patient", render: (row) => row.patient_name },
    { key: "waiting_since", header: "Waiting", align: "right", render: (row) => formatDurationSince(row.created_at) },
  ];

  return (
    <div>
      <PageHeader title="Dashboard" description="Today's operational snapshot." />

      {summaryError ? (
        <div className={styles.kpiGrid}>
          <ErrorState description="Could not load dashboard KPIs." onRetry={refetchSummary} />
        </div>
      ) : (
        <div className={styles.kpiGrid}>
          <KpiCard label="Orders Today" value={summary?.orders_today ?? 0} isLoading={summaryLoading} />
          <KpiCard label="Completed Today" value={summary?.completed_today ?? 0} tone="success" isLoading={summaryLoading} />
          <KpiCard label="Pending" value={summary?.pending_orders ?? 0} tone="warning" isLoading={summaryLoading} />
          <KpiCard
            label="Avg. Fulfilment Time"
            value={formatMinutes(summary?.average_fulfilment_minutes)}
            isLoading={summaryLoading}
          />
          <KpiCard label="Low Stock" value={summary?.low_stock_drugs ?? 0} tone="warning" isLoading={summaryLoading} />
          <KpiCard
            label="Critical / Urgent Reorder"
            value={summary?.critical_stock_drugs ?? 0}
            tone="danger"
            isLoading={summaryLoading}
          />
        </div>
      )}

      <div className={styles.mainGrid}>
        <section>
          <h2 className={styles.sectionTitle}>Recent Orders</h2>
          <DataTable
            columns={recentColumns}
            rows={recentOrders?.items ?? []}
            rowKey={(row) => row.id}
            onRowClick={(row) => navigate(`/orders/${row.id}`)}
            isLoading={recentLoading}
            isError={recentError}
            onRetry={refetchRecent}
            emptyTitle="No recent orders"
          />
        </section>

        <div className={styles.sideColumn}>
          <section>
            <h2 className={styles.sectionTitle}>Low / Critical Stock</h2>
            <DataTable
              columns={lowStockColumns}
              rows={lowStock ?? []}
              rowKey={(row) => row.drug_id}
              onRowClick={() => navigate("/inventory")}
              isLoading={lowStockLoading}
              isError={lowStockError}
              onRetry={refetchLowStock}
              emptyTitle="All stock healthy"
              emptyDescription="No drugs currently need attention."
            />
          </section>

          <section>
            <h2 className={styles.sectionTitle}>Pending Orders</h2>
            <DataTable
              columns={pendingColumns}
              rows={pendingOrders?.items ?? []}
              rowKey={(row) => row.id}
              onRowClick={(row) => navigate(`/orders/${row.id}`)}
              isLoading={pendingLoading}
              isError={pendingError}
              onRetry={refetchPending}
              emptyTitle="No pending orders"
              emptyDescription="All orders are being fulfilled."
            />
          </section>
        </div>
      </div>
    </div>
  );
}
