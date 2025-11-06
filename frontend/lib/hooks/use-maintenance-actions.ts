"use client";

import { useState } from "react";
import { MaintenanceService, ApiError } from "@/lib/api/generated";
import { toast } from "sonner";
import { logger } from "@/lib/utils/logger";

export type ActionType = "q" | "m" | "all";

type LoadingState = Record<ActionType, boolean>;

interface UseMaintenanceActionsOptions {
  onSuccess?: () => void;
}

const SUCCESS_MESSAGES: Record<ActionType, string> = {
  q: "Cleared Qdrant collection",
  m: "Cleared MinIO bucket",
  all: "Cleared all stored data",
};

/**
 * Hook to manage maintenance actions (clear operations)
 */
export function useMaintenanceActions({ onSuccess }: UseMaintenanceActionsOptions = {}) {
  const [loading, setLoading] = useState<LoadingState>({ q: false, m: false, all: false });

  const actionHandlers: Record<ActionType, () => Promise<unknown>> = {
    q: () => MaintenanceService.clearQdrantClearQdrantPost(),
    m: () => MaintenanceService.clearMinioClearMinioPost(),
    all: () => MaintenanceService.clearAllClearAllPost(),
  };

  const runAction = async (action: ActionType) => {
    const handler = actionHandlers[action];
    if (!handler) {
      return;
    }

    setLoading((state) => ({ ...state, [action]: true }));

    try {
      const response = await handler();

      const description = typeof response === "object" && response !== null
        ? ("message" in response && typeof response.message === "string" ? response.message : JSON.stringify(response))
        : String(response ?? "Operation completed successfully");

      toast.success(SUCCESS_MESSAGES[action], { description });

      try {
        if (typeof localStorage !== "undefined") {
          const previous = Number.parseInt(localStorage.getItem("maintenance_operations") ?? "0", 10) || 0;
          localStorage.setItem("maintenance_operations", String(previous + 1));
          localStorage.setItem("last_maintenance_action", new Date().toISOString());
        }
      } catch {
        // Ignore storage errors; they should not block the action.
      }

      onSuccess?.();
      window.dispatchEvent(new CustomEvent("systemStatusChanged"));
    } catch (err: unknown) {
      let message = "Maintenance action failed";
      if (err instanceof ApiError) {
        message = `${err.status}: ${err.message}`;
        logger.error('Maintenance action failed', { error: err, action, status: err.status });
      } else if (err instanceof Error) {
        message = err.message;
        logger.error('Maintenance action failed', { error: err, action });
      }
      toast.error("Action failed", { description: message });
    } finally {
      setLoading((state) => ({ ...state, [action]: false }));
    }
  };

  return { loading, runAction };
}
