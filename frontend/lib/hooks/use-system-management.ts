import { useState } from "react";
import { MaintenanceService, ApiError } from "@/lib/api/generated";
import { toast } from "@/components/ui/sonner";

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

  const handleInitialize = async () => {
    setInitLoading(true);
    try {
      const result = await MaintenanceService.initializeInitializePost();
      
      if (result.status === "success") {
        toast.success("Initialization Complete", { 
          description: "Collection is ready (and MinIO bucket if enabled)" 
        });
      } else if (result.status === "partial") {
        toast.warning("Partial Initialization", { 
          description: "Some components failed to initialize. Check details." 
        });
      } else {
        toast.error("Initialization Failed", { 
          description: "Failed to initialize required storage components" 
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
      
      if (result.status === "success") {
        toast.success("Deletion Complete", { 
          description: "Collection removed (and MinIO bucket if enabled)" 
        });
      } else if (result.status === "partial") {
        toast.warning("Partial Deletion", { 
          description: "Some components failed to delete. Check details." 
        });
      } else {
        toast.error("Deletion Failed", { 
          description: "Failed to delete required storage components" 
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
