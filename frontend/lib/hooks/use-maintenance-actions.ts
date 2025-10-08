import { useState } from "react";
import { toast } from "@/components/ui/sonner";
import { zodClient } from "@/lib/api/client";
import { getErrorMessage } from "@/lib/api/errors";
import { ActionType, LoadingState } from "@/components/maintenance/types";
import { MAINTENANCE_ACTIONS } from "@/components/maintenance/constants";


interface UseMaintenanceActionsOptions {
  onSuccess?: () => void;
}

/**
 * Hook to manage maintenance actions (clear operations)
 */
export function useMaintenanceActions({ onSuccess }: UseMaintenanceActionsOptions = {}) {
  const [loading, setLoading] = useState<LoadingState>({ q: false, m: false, all: false });
  const [dialogOpen, setDialogOpen] = useState<ActionType | null>(null);

  const actionHandlers: Record<ActionType, () => Promise<unknown>> = {
    q: () => zodClient.post("/clear/qdrant"),
    m: () => zodClient.post("/clear/minio"),
    all: () => zodClient.post("/clear/all"),
  };

  const runAction = async (action: ActionType) => {
    const actionConfig = MAINTENANCE_ACTIONS.find(a => a.id === action);
    if (!actionConfig) return;

    const handler = actionHandlers[action];
    if (!handler) return;

    setLoading((s) => ({ ...s, [action]: true }));
    setDialogOpen(null);

    try {
      const res = await handler();

      const msg = typeof res === "object" && res !== null
        ? ('message' in res && typeof res.message === 'string' ? res.message : JSON.stringify(res))
        : String(res ?? "Operation completed successfully");

      toast.success(actionConfig.successMsg, { description: msg });

      // Update stats
      try {
        if (typeof localStorage !== "undefined") {
          const prevTotal = Number.parseInt(localStorage.getItem("maintenance_operations") ?? "0", 10) || 0;
          const newTotal = prevTotal + 1;
          localStorage.setItem("maintenance_operations", newTotal.toString());
          localStorage.setItem("last_maintenance_action", new Date().toISOString());
        }
      } catch {
        // Swallow storage exceptions so the action can still complete
      }
      
      // Notify success callback
      onSuccess?.();
      
      // Dispatch event to notify other pages
      window.dispatchEvent(new CustomEvent('systemStatusChanged'));
    } catch (err: unknown) {
      const errorMsg = getErrorMessage(err, "Maintenance action failed");
      toast.error("Action failed", { description: errorMsg });
    } finally {
      setLoading((s) => ({ ...s, [action]: false }));
    }
  };

  const isAnyLoading = loading.q || loading.m || loading.all;

  return {
    loading,
    dialogOpen,
    setDialogOpen,
    runAction,
    isAnyLoading,
  };
}
