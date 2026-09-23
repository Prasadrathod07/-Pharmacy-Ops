import { Badge, type BadgeTone } from "./Badge";

const STATUS_MAP: Record<string, { label: string; tone: BadgeTone }> = {
  // Order / order item status
  NEW: { label: "New", tone: "neutral" },
  WAITING_FOR_STOCK: { label: "Waiting for Stock", tone: "warning" },
  DISPENSED: { label: "Dispensed", tone: "info" },
  COMPLETED: { label: "Completed", tone: "success" },
  CANCELLED: { label: "Cancelled", tone: "neutral" },
  PENDING: { label: "Pending", tone: "neutral" },

  // Stock status
  HEALTHY: { label: "Healthy", tone: "success" },
  LOW_STOCK: { label: "Low Stock", tone: "warning" },
  CRITICAL: { label: "Critical", tone: "danger" },
  OUT_OF_STOCK: { label: "Out of Stock", tone: "danger" },

  // Inventory movement type
  RESTOCK: { label: "Restock", tone: "success" },
  DISPENSE: { label: "Dispense", tone: "info" },
  ADJUSTMENT: { label: "Adjustment", tone: "neutral" },
};

export function StatusBadge({ status }: { status: string }) {
  const entry = STATUS_MAP[status] ?? { label: status, tone: "neutral" as BadgeTone };
  return <Badge tone={entry.tone}>{entry.label}</Badge>;
}
