import { useEffect } from "react";
import { useQueryClient } from "@tanstack/react-query";

import { API_BASE_URL } from "../api/client";
import { dashboardKeys } from "../features/dashboard/keys";
import { inventoryKeys } from "../features/inventory/keys";
import { orderKeys } from "../features/orders/keys";

const REALTIME_ENABLED = import.meta.env.VITE_ENABLE_REALTIME === "true";

/**
 * Subscribes to the backend's SSE stream and invalidates the relevant
 * TanStack Query keys on order/inventory/dashboard events, so open pages
 * refresh without polling (master spec §42).
 *
 * This is a pure UI convenience layer, not a correctness mechanism:
 * - If VITE_ENABLE_REALTIME is unset/false, this is a no-op entirely.
 * - EventSource reconnects automatically on drop (native browser behavior);
 *   we don't add custom retry logic on top of it.
 * - If the stream never connects or silently degrades, mutations already
 *   invalidate their own affected queries directly (see features/*\/hooks.ts),
 *   so the UI never depends on this connection to stay correct - only to
 *   refresh faster / reflect changes made by other clients.
 */
export function useRealtimeEvents(): void {
  const queryClient = useQueryClient();

  useEffect(() => {
    if (!REALTIME_ENABLED) return;

    const source = new EventSource(`${API_BASE_URL}/events/stream`);

    const invalidateOrders = () => queryClient.invalidateQueries({ queryKey: orderKeys.all });
    const invalidateInventory = () => queryClient.invalidateQueries({ queryKey: inventoryKeys.all });
    const invalidateDashboard = () => queryClient.invalidateQueries({ queryKey: dashboardKeys.all });

    source.addEventListener("order.created", invalidateOrders);
    source.addEventListener("order.updated", invalidateOrders);
    source.addEventListener("inventory.updated", invalidateInventory);
    source.addEventListener("dashboard.updated", invalidateDashboard);

    source.onerror = () => {
      // EventSource retries on its own; this is just a visibility log,
      // never surfaced to the user (see module docstring).
      console.warn("Realtime event stream disconnected; browser will retry automatically.");
    };

    return () => {
      source.close();
    };
  }, [queryClient]);
}
