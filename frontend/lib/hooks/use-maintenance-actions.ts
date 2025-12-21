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
  q: "Qdrant collection reset",
  m: "Storage bucket reset",
  all: "Reset All Data",
};

const SERVICE_LABELS: Record<string, string> = {
  collection: "Qdrant",
  bucket: "Storage",
  duckdb: "DuckDB",
};

interface ServiceResult {
  status: "success" | "skipped" | "error" | "pending";
  message: string;
}

const summarizeResults = (result: any) => {
  const entries = result?.results;
  if (!entries || typeof entries !== "object") {
    return undefined;
  }

  const completed: string[] = [];
  const skipped: string[] = [];
  const failed: string[] = [];

  for (const [key, value] of Object.entries(entries) as [string, ServiceResult][]) {
    const label = SERVICE_LABELS[key] ?? key;
    switch (value?.status) {
      case "success":
        completed.push(label);
        break;
      case "skipped":
        skipped.push(label);
        break;
      case "error":
        failed.push(label);
        break;
      default:
        break;
    }
  }

  const parts: string[] = [];
  if (completed.length) parts.push(`Completed: ${completed.join(", ")}`);
  if (skipped.length) parts.push(`Skipped: ${skipped.join(", ")}`);
  if (failed.length) parts.push(`Failed: ${failed.join(", ")}`);

  return parts.length ? parts.join(" • ") : undefined;
};

/**
 * Hook to manage maintenance actions (clear operations)
 */
export function useMaintenanceActions({ onSuccess }: UseMaintenanceActionsOptions = {}) {
  const [loading, setLoading] = useState<LoadingState>({ q: false, m: false, all: false });

  const actionHandlers: Record<ActionType, () => Promise<unknown>> = {
    q: () => MaintenanceService.clearQdrantClearQdrantPost(),
    m: () => MaintenanceService.clearStorageClearStoragePost(),
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

      if (action === "all" && typeof response === "object" && response !== null) {
        const responseObj = response as Record<string, unknown>;
        const status: string | undefined =
          typeof responseObj.status === "string" ? responseObj.status : undefined;
        const description = summarizeResults(responseObj);

        if (status === "success") {
          toast.success(SUCCESS_MESSAGES[action], description ? { description } : undefined);
        } else if (status === "partial") {
          toast.warning("Partial Reset", description ? { description } : undefined);
        } else {
          toast.error("Reset Failed", description ? { description } : undefined);
        }
      } else {
        toast.success(SUCCESS_MESSAGES[action]);
      }

      try {
        if (typeof localStorage !== "undefined") {
          const previous = Number.parseInt(localStorage.getItem("maintenance_operations") ?? "0", 10) || 0;
          localStorage.setItem("maintenance_operations", String(previous + 1));
          localStorage.setItem("last_maintenance_action", new Date().toISOString());
        }
      } catch (storageError) {
        logger.warn("Failed to update maintenance stats in localStorage", { error: storageError });
        toast.error("Failed to update maintenance stats in localStorage", { description: String(storageError) });
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
