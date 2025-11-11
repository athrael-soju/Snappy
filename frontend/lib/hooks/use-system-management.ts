import { useState } from "react";
import { MaintenanceService, ApiError } from "@/lib/api/generated";
import { toast } from "sonner";
import { logger } from "@/lib/utils/logger";

interface UseSystemManagementOptions {
  onSuccess?: () => void;
}

/**
 * Hook to manage system initialization and deletion
 */
export function useSystemManagement({ onSuccess }: UseSystemManagementOptions = {}) {
  const [initLoading, setInitLoading] = useState(false);
  const [deleteLoading, setDeleteLoading] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);

  const buildSuccessDescription = (result: any, fallback: string) => {
    const descriptions: string[] = [];

    const bucketMessage = result?.results?.bucket?.message;
    if (typeof bucketMessage === "string" && bucketMessage.length > 0) {
      descriptions.push(bucketMessage);
    }

    const duckdbMessage = result?.results?.duckdb?.message;
    if (typeof duckdbMessage === "string" && duckdbMessage.length > 0) {
      descriptions.push(duckdbMessage);
    }

    if (descriptions.length > 0) {
      return descriptions.join(" • ");
    }

    return fallback;
  };

  const handleInitialize = async () => {
    setInitLoading(true);
    try {
      const result = await MaintenanceService.initializeInitializePost();

      const status: string | undefined = typeof result?.status === "string" ? result.status : undefined;

      if (status === "success") {
        toast.success("Initialization Complete", {
          description: buildSuccessDescription(result, "Qdrant collection and MinIO bucket are ready"),
        });
      } else if (status === "partial") {
        toast.warning("Partial Initialization", {
          description: "Some components failed to initialize. Check details.",
        });
      } else {
        toast.error("Initialization Failed", {
          description: "Failed to initialize required storage components",
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

      if (status === "success") {
        toast.success("Deletion Complete", {
          description: buildSuccessDescription(result, "Qdrant collection and MinIO bucket removed"),
        });
      } else if (status === "partial") {
        toast.warning("Partial Deletion", {
          description: "Some components failed to delete. Check details.",
        });
      } else {
        toast.error("Deletion Failed", {
          description: "Failed to delete required storage components",
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
