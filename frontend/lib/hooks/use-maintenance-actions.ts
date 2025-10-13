import { useState } from "react";
import { MaintenanceService, ApiError } from "@/lib/api/generated";
import { toast } from "@/components/ui/sonner";
import { ActionType, LoadingState } from "@/components/maintenance/types";
import { MAINTENANCE_ACTIONS } from "@/components/maintenance/constants";
import { useAppStore } from "@/stores/app-store";


interface UseMaintenanceActionsOptions {
  onSuccess?: () => void;
}

/**
 * Hook to manage maintenance actions (clear operations)
 */
export function useMaintenanceActions({ onSuccess }: UseMaintenanceActionsOptions = {}) {
  const [loading, setLoading] = useState<LoadingState>({ q: false, m: false, all: false });
  const [dialogOpen, setDialogOpen] = useState<ActionType | null>(null);
  const { state } = useAppStore();
  const isMinioDisabled = state.systemStatus?.bucket?.disabled === true;

  const actionHandlers: Record<ActionType, () => Promise<unknown>> = {
    q: () => MaintenanceService.clearQdrantClearQdrantPost(),
    m: () => MaintenanceService.clearMinioClearMinioPost(),
    all: () => MaintenanceService.clearAllClearAllPost(),
  };

  const runAction = async (action: ActionType) => {
    const actionConfig = MAINTENANCE_ACTIONS.find(a => a.id === action);
    if (!actionConfig) return;

    const handler = actionHandlers[action];
    if (!handler) return;

    if (action === "m" && isMinioDisabled) {
      toast.info("MinIO Disabled", {
        description: "MinIO is disabled via configuration; there is nothing to clear.",
      });
      setDialogOpen(null);
      return;
    }

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
      let errorMsg = "Maintenance action failed";
      if (err instanceof ApiError) {
        errorMsg = `${err.status}: ${err.message}`;
      } else if (err instanceof Error) {
        errorMsg = err.message;
      }
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
