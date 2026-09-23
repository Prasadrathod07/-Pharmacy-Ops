import { Badge, DataTable, type DataTableColumn, Modal, StatusBadge } from "../../../components/ui";
import { useInventoryTransactions } from "../hooks";
import type { InventoryTransaction } from "../../../types";
import { formatDateTime } from "../../../utils/format";

interface InventoryDetailModalProps {
  drugId: number;
  drugName: string;
  onClose: () => void;
}

export function InventoryDetailModal({ drugId, drugName, onClose }: InventoryDetailModalProps) {
  const { data, isLoading, isError, refetch } = useInventoryTransactions(drugId, { page_size: 20 });

  const columns: DataTableColumn<InventoryTransaction>[] = [
    { key: "created_at", header: "When", render: (txn) => formatDateTime(txn.created_at) },
    { key: "movement_type", header: "Type", render: (txn) => <StatusBadge status={txn.movement_type} /> },
    { key: "delta", header: "Delta", align: "right", render: (txn) => (txn.quantity_delta > 0 ? `+${txn.quantity_delta}` : txn.quantity_delta) },
    { key: "before_after", header: "Before → After", align: "right", render: (txn) => `${txn.quantity_before} → ${txn.quantity_after}` },
    {
      key: "order",
      header: "Order",
      render: (txn) => (txn.order_id ? <Badge tone="info" dot={false}>#{txn.order_id}</Badge> : "—"),
    },
    { key: "note", header: "Note", render: (txn) => txn.note ?? "—" },
  ];

  return (
    <Modal title={`${drugName} — Movement History`} onClose={onClose} size="lg">
      <div>
        <DataTable
          columns={columns}
          rows={data?.items ?? []}
          rowKey={(txn) => txn.id}
          isLoading={isLoading}
          isError={isError}
          onRetry={refetch}
          emptyTitle="No movements yet"
          emptyDescription="Inventory transactions for this drug will appear here."
        />
      </div>
    </Modal>
  );
}
