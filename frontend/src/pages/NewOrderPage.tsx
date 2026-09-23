import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { useToast } from "../components/feedback";
import { Badge, Button, DataTable, type DataTableColumn, FormField, Input, PageHeader } from "../components/ui";
import { DrugPicker } from "../features/orders/components/DrugPicker";
import { useCreateOrder } from "../features/orders/hooks";
import type { DrugListItem } from "../types";

interface DraftItem {
  drugId: number;
  drugCode: string;
  drugName: string;
  currentStock: number;
  quantity: number;
}

function availabilityFor(item: DraftItem): { label: string; tone: "success" | "warning" | "danger" } {
  if (item.currentStock === 0) return { label: "Out of Stock", tone: "danger" };
  if (item.quantity <= item.currentStock) return { label: "Available", tone: "success" };
  return { label: `Short by ${item.quantity - item.currentStock}`, tone: "warning" };
}

export function NewOrderPage() {
  const navigate = useNavigate();
  const { showToast } = useToast();
  const createOrder = useCreateOrder();

  const [patientName, setPatientName] = useState("");
  const [orderedAt, setOrderedAt] = useState("");
  const [items, setItems] = useState<DraftItem[]>([]);
  const [formError, setFormError] = useState<string | null>(null);

  function handleSelectDrug(drug: DrugListItem) {
    setItems((current) => [
      ...current,
      { drugId: drug.id, drugCode: drug.code, drugName: drug.name, currentStock: drug.quantity_on_hand, quantity: 1 },
    ]);
  }

  function updateQuantity(drugId: number, quantity: number) {
    setItems((current) => current.map((item) => (item.drugId === drugId ? { ...item, quantity } : item)));
  }

  function removeItem(drugId: number) {
    setItems((current) => current.filter((item) => item.drugId !== drugId));
  }

  const hasInvalidQuantity = items.some((item) => !Number.isInteger(item.quantity) || item.quantity <= 0);
  const canSubmit = patientName.trim().length > 0 && items.length > 0 && !hasInvalidQuantity;

  async function handleSubmit() {
    setFormError(null);
    if (!canSubmit) {
      setFormError("Enter a patient name and at least one medicine with a valid quantity.");
      return;
    }

    try {
      const order = await createOrder.mutateAsync({
        patient_name: patientName,
        ordered_at: orderedAt ? new Date(orderedAt).toISOString() : undefined,
        items: items.map((item) => ({ drug_id: item.drugId, quantity: item.quantity })),
      });

      if (order.status === "DISPENSED") {
        showToast(`Order ${order.order_number} dispensed successfully.`, "success");
      } else if (order.status === "WAITING_FOR_STOCK") {
        showToast(`Order ${order.order_number} created - waiting for stock on one or more items.`, "info");
      } else {
        showToast(`Order ${order.order_number} created.`, "success");
      }

      navigate(`/orders/${order.id}`);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Could not create order.";
      setFormError(message);
      showToast(message, "error");
    }
  }

  const columns: DataTableColumn<DraftItem>[] = [
    { key: "drug", header: "Medicine", render: (item) => `${item.drugName} (${item.drugCode})` },
    { key: "stock", header: "Current Stock", align: "right", render: (item) => item.currentStock },
    {
      key: "quantity",
      header: "Requested Qty",
      align: "right",
      render: (item) => (
        <Input
          type="number"
          min={1}
          step={1}
          value={item.quantity}
          style={{ width: 90, textAlign: "right" }}
          onChange={(event) => updateQuantity(item.drugId, Number(event.target.value))}
        />
      ),
    },
    {
      key: "result",
      header: "Result",
      render: (item) => {
        const { label, tone } = availabilityFor(item);
        return <Badge tone={tone}>{label}</Badge>;
      },
    },
    {
      key: "remove",
      header: "",
      render: (item) => (
        <Button variant="ghost" size="sm" onClick={() => removeItem(item.drugId)}>
          Remove
        </Button>
      ),
    },
  ];

  return (
    <div>
      <PageHeader title="New Order" description="Capture a prescription order for a patient." />

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14, maxWidth: 640, marginBottom: 20 }}>
        <FormField label="Patient Name">
          <Input
            value={patientName}
            onChange={(event) => setPatientName(event.target.value)}
            placeholder="e.g. Alex Johnson"
          />
        </FormField>
        <FormField label="Order Date/Time (optional)" hint="Defaults to now if left blank">
          <Input type="datetime-local" value={orderedAt} onChange={(event) => setOrderedAt(event.target.value)} />
        </FormField>
      </div>

      <FormField label="Add Medicine">
        <div style={{ maxWidth: 420 }}>
          <DrugPicker onSelect={handleSelectDrug} excludeDrugIds={items.map((item) => item.drugId)} />
        </div>
      </FormField>

      <div style={{ marginTop: 16, marginBottom: 16 }}>
        <DataTable
          columns={columns}
          rows={items}
          rowKey={(item) => item.drugId}
          emptyTitle="No medicines added yet"
          emptyDescription="Search and add at least one medicine above."
        />
      </div>

      <p style={{ fontSize: 12.5, color: "var(--color-text-muted)", marginBottom: 16 }}>
        Stock shown above is informational. The system re-checks actual availability when you confirm the order.
      </p>

      {formError ? (
        <p style={{ fontSize: 13, color: "var(--color-danger)", marginBottom: 12 }}>{formError}</p>
      ) : null}

      <Button onClick={handleSubmit} disabled={!canSubmit || createOrder.isPending}>
        {createOrder.isPending ? "Confirming..." : "Confirm Order"}
      </Button>
    </div>
  );
}
