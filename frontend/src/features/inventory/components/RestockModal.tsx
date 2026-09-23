import { useState } from "react";

import { useToast } from "../../../components/feedback";
import { Button, FormField, Input, Modal, StatusBadge } from "../../../components/ui";
import { useRestock } from "../hooks";
import type { InventoryListItem } from "../../../types";

interface RestockModalProps {
  item: InventoryListItem;
  onClose: () => void;
}

export function RestockModal({ item, onClose }: RestockModalProps) {
  const { showToast } = useToast();
  const restock = useRestock(item.drug_id);

  const [quantity, setQuantity] = useState("");
  const [note, setNote] = useState("");
  const [error, setError] = useState<string | null>(null);

  const parsedQuantity = Number(quantity);
  const isValidQuantity = quantity.trim() !== "" && Number.isInteger(parsedQuantity) && parsedQuantity > 0;

  async function handleSubmit() {
    setError(null);
    if (!isValidQuantity) {
      setError("Enter a whole number greater than zero.");
      return;
    }
    if (!window.confirm(`Restock ${item.drug_name} by ${parsedQuantity} units?`)) return;

    try {
      const updated = await restock.mutateAsync({ quantity: parsedQuantity, note: note.trim() || undefined });
      showToast(
        `Restocked ${item.drug_name}: ${item.quantity_on_hand} → ${updated.quantity_on_hand} units.`,
        "success",
      );
      onClose();
    } catch (err) {
      const message = err instanceof Error ? err.message : "Could not restock this drug.";
      setError(message);
      showToast(message, "error");
    }
  }

  return (
    <Modal title={`Restock ${item.drug_name}`} onClose={onClose}>
      <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <span style={{ fontSize: 13, color: "var(--color-text-secondary)" }}>Current stock</span>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <strong>{item.quantity_on_hand}</strong>
            <StatusBadge status={item.status} />
          </div>
        </div>

        <FormField label="Restock quantity" error={error ?? undefined}>
          <Input
            type="number"
            min={1}
            step={1}
            value={quantity}
            onChange={(event) => setQuantity(event.target.value)}
            placeholder="e.g. 100"
            autoFocus
          />
        </FormField>

        <FormField label="Note (optional)">
          <Input value={note} onChange={(event) => setNote(event.target.value)} placeholder="e.g. Supplier delivery #4521" />
        </FormField>

        <div style={{ display: "flex", justifyContent: "flex-end", gap: 8 }}>
          <Button variant="secondary" onClick={onClose} disabled={restock.isPending}>
            Cancel
          </Button>
          <Button onClick={handleSubmit} disabled={restock.isPending}>
            {restock.isPending ? "Restocking..." : "Confirm Restock"}
          </Button>
        </div>
      </div>
    </Modal>
  );
}
