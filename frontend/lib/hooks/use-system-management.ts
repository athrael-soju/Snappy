import { useState } from "react";
import { MaintenanceService, ApiError } from "@/lib/api/generated";
import { toast } from "sonner";

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
    const message = result?.results?.bucket?.message;
    if (typeof message === "string" && message.length > 0) {
      return message;
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
          description: buildSuccessDescription(result, "Qdrant Collection & MinIO bucket ready"),
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
      } else if (err instanceof Error) {
        errorMsg = err.message;
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
          description: buildSuccessDescription(result, "Collection removed (and MinIO bucket if enabled)"),
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
      } else if (err instanceof Error) {
        errorMsg = err.message;
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
