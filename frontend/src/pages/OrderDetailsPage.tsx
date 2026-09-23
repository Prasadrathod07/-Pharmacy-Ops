import type { ReactNode } from "react";
import { useNavigate, useParams } from "react-router-dom";

import { useToast } from "../components/feedback";
import { Button, DataTable, type DataTableColumn, PageHeader, StatusBadge } from "../components/ui";
import { ErrorState } from "../components/feedback/ErrorState";
import { SkeletonStack } from "../components/feedback/Skeleton";
import { useCancelOrder, useCompleteOrder, useOrder } from "../features/orders/hooks";
import type { OrderItem } from "../types";
import { formatDateTime } from "../utils/format";

export function OrderDetailsPage() {
  const params = useParams<{ orderId: string }>();
  const orderId = params.orderId ? Number(params.orderId) : undefined;
  const navigate = useNavigate();
  const { showToast } = useToast();

  const { data: order, isLoading, isError, refetch } = useOrder(orderId);
  const completeOrder = useCompleteOrder();
  const cancelOrder = useCancelOrder();

  if (!orderId || Number.isNaN(orderId)) {
    return <ErrorState title="Invalid order" description="No valid order ID was provided." />;
  }

  if (isLoading) {
    return (
      <div>
        <PageHeader title="Order Details" />
        <SkeletonStack rows={6} />
      </div>
    );
  }

  if (isError || !order) {
    return (
      <div>
        <PageHeader title="Order Details" />
        <ErrorState description="Could not load this order." onRetry={refetch} />
      </div>
    );
  }

  const canComplete = order.status === "DISPENSED";
  const canCancel = order.status === "NEW" || order.status === "WAITING_FOR_STOCK";

  async function handleComplete() {
    try {
      await completeOrder.mutateAsync(orderId as number);
      showToast("Order marked as completed.", "success");
    } catch (error) {
      showToast(error instanceof Error ? error.message : "Could not complete order.", "error");
    }
  }

  async function handleCancel() {
    if (!window.confirm("Cancel this order? This cannot be undone.")) return;
    try {
      await cancelOrder.mutateAsync(orderId as number);
      showToast("Order cancelled.", "info");
    } catch (error) {
      showToast(error instanceof Error ? error.message : "Could not cancel order.", "error");
    }
  }

  const itemColumns: DataTableColumn<OrderItem>[] = [
    { key: "drug", header: "Medicine", render: (item) => `${item.drug_name} (${item.drug_code})` },
    { key: "requested", header: "Requested", align: "right", render: (item) => item.requested_quantity },
    { key: "dispensed", header: "Dispensed", align: "right", render: (item) => item.dispensed_quantity },
    { key: "status", header: "Status", render: (item) => <StatusBadge status={item.status} /> },
  ];

  return (
    <div>
      <PageHeader
        title={order.order_number}
        description={`Patient: ${order.patient_name}`}
        actions={
          <>
            <Button variant="secondary" size="sm" onClick={() => navigate("/orders")}>
              Back to Orders
            </Button>
            {canCancel ? (
              <Button variant="secondary" size="sm" onClick={handleCancel} disabled={cancelOrder.isPending}>
                {cancelOrder.isPending ? "Cancelling..." : "Cancel Order"}
              </Button>
            ) : null}
            {canComplete ? (
              <Button size="sm" onClick={handleComplete} disabled={completeOrder.isPending}>
                {completeOrder.isPending ? "Completing..." : "Mark Completed"}
              </Button>
            ) : null}
          </>
        }
      />

      <div style={{ display: "flex", gap: 12, marginBottom: 20, flexWrap: "wrap" }}>
        <SummaryTile label="Status" value={<StatusBadge status={order.status} />} />
        <SummaryTile label="Created" value={formatDateTime(order.created_at)} />
        <SummaryTile label="Dispensed" value={formatDateTime(order.dispensed_at)} />
        <SummaryTile label="Completed" value={formatDateTime(order.completed_at)} />
        {order.cancelled_at ? <SummaryTile label="Cancelled" value={formatDateTime(order.cancelled_at)} /> : null}
      </div>

      <DataTable columns={itemColumns} rows={order.items} rowKey={(item) => item.id} emptyTitle="No items on this order" />
    </div>
  );
}

function SummaryTile({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div
      style={{
        background: "var(--color-surface)",
        border: "1px solid var(--color-border)",
        borderRadius: "var(--radius-md)",
        padding: "10px 14px",
        minWidth: 140,
      }}
    >
      <div style={{ fontSize: 11.5, color: "var(--color-text-muted)", marginBottom: 4 }}>{label}</div>
      <div style={{ fontSize: 13.5, fontWeight: 600 }}>{value}</div>
    </div>
  );
}
