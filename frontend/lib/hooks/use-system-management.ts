import { useState } from "react";
import { MaintenanceService, ApiError } from "@/lib/api/generated";
import { toast } from "sonner";
import { logger } from "@/lib/utils/logger";

interface UseSystemManagementOptions {
  onSuccess?: () => void;
}

const SERVICE_LABELS: Record<string, string> = {
  collection: "Qdrant",
  bucket: "MinIO",
  duckdb: "DuckDB",
};

const summarizeResults = (result: any): string | undefined => {
  const entries = result?.results;
  if (!entries || typeof entries !== "object") {
    return undefined;
  }

  const completed: string[] = [];
  const skipped: string[] = [];
  const failed: string[] = [];

  for (const [key, value] of Object.entries(entries)) {
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
 * Hook to manage system initialization and deletion
 */
export function useSystemManagement({ onSuccess }: UseSystemManagementOptions = {}) {
  const [initLoading, setInitLoading] = useState(false);
  const [deleteLoading, setDeleteLoading] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);

  const handleInitialize = async () => {
    setInitLoading(true);
    try {
      const result = await MaintenanceService.initializeInitializePost();

      const status: string | undefined = typeof result?.status === "string" ? result.status : undefined;

      const summary = summarizeResults(result);

      if (status === "success") {
        toast.success("Initialization Complete", {
          description: summary ?? "Qdrant collection, MinIO bucket and DuckDB Database are ready",
        });
      } else if (status === "partial") {
        toast.warning("Partial Initialization", {
          description: summary ?? "Some components failed to initialize.",
        });
      } else {
        toast.error("Initialization Failed", {
          description: summary ?? "Failed to initialize required storage components",
        });
      }

      // Notify success callback
      onSuccess?.();

      // Dispatch event to notify other pages
      window.dispatchEvent(new CustomEvent('systemStatusChanged'));
    } catch (err: unknown) {
      let errorMsg = "Initialization failed";
      if (err instanceof ApiError) {
        errorMsg = `${err.status}: ${err.message}`;
        logger.error('System initialization failed', { error: err, status: err.status });
      } else if (err instanceof Error) {
        errorMsg = err.message;
        logger.error('System initialization failed', { error: err });
      }
      toast.error("Initialization Failed", { description: errorMsg });
    } finally {
      setInitLoading(false);
    }
  };

  const handleDelete = async () => {
    setDeleteLoading(true);
    setDeleteDialogOpen(false);
    try {
      const result = await MaintenanceService.deleteCollectionAndBucketDeleteDelete();

      const status: string | undefined = typeof result?.status === "string" ? result.status : undefined;

      const summary = summarizeResults(result);

      if (status === "success") {
        toast.success("Deletion Complete", {
          description: summary ?? "Qdrant collection and MinIO bucket removed",
        });
      } else if (status === "partial") {
        toast.warning("Partial Deletion", {
          description: summary ?? "Some components failed to delete.",
        });
      } else {
        toast.error("Deletion Failed", {
          description: summary ?? "Failed to delete required storage components",
        });
      }

      // Notify success callback
      onSuccess?.();

      // Dispatch event to notify other pages
      window.dispatchEvent(new CustomEvent('systemStatusChanged'));
    } catch (err: unknown) {
      let errorMsg = "Deletion failed";
      if (err instanceof ApiError) {
        errorMsg = `${err.status}: ${err.message}`;
        logger.error('System deletion failed', { error: err, status: err.status });
      } else if (err instanceof Error) {
        errorMsg = err.message;
        logger.error('System deletion failed', { error: err });
      }
      toast.error("Deletion Failed", { description: errorMsg });
    } finally {
      setDeleteLoading(false);
    }
  };

  return {
    initLoading,
    deleteLoading,
    deleteDialogOpen,
    setDeleteDialogOpen,
    handleInitialize,
    handleDelete,
  };
}
