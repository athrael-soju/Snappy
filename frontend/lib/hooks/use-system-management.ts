import { useState } from "react";
import { toast } from "@/components/ui/sonner";
import { zodClient } from "@/lib/api/client";
import { getErrorMessage } from "@/lib/api/errors";

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
      const result = await zodClient.post("/initialize");
      const status = (result as { status?: string })?.status ?? "unknown";
      
      if (status === "success") {
        toast.success("Initialization Complete", { 
          description: "Collection and bucket are ready to use" 
        });
      } else if (status === "partial") {
        toast.warning("Partial Initialization", { 
          description: "Some components failed to initialize. Check details." 
        });
      } else {
        toast.error("Initialization Failed", { 
          description: "Failed to initialize collection and bucket" 
        });
      }
      
      // Notify success callback
      onSuccess?.();
      
      // Dispatch event to notify other pages
      window.dispatchEvent(new CustomEvent('systemStatusChanged'));
    } catch (err: unknown) {
      const errorMsg = getErrorMessage(err, "Initialization failed");
      toast.error("Initialization Failed", { description: errorMsg });
    } finally {
      setInitLoading(false);
    }
  };

  const handleDelete = async () => {
    setDeleteLoading(true);
    setDeleteDialogOpen(false);
    try {
      const result = await zodClient.post("/delete");
      const status = (result as { status?: string })?.status ?? "unknown";
      
      if (status === "success") {
        toast.success("Deletion Complete", { 
          description: "Collection and bucket have been deleted" 
        });
      } else if (status === "partial") {
        toast.warning("Partial Deletion", { 
          description: "Some components failed to delete. Check details." 
        });
      } else {
        toast.error("Deletion Failed", { 
          description: "Failed to delete collection and bucket" 
        });
      }
      
      // Notify success callback
      onSuccess?.();
      
      // Dispatch event to notify other pages
      window.dispatchEvent(new CustomEvent('systemStatusChanged'));
    } catch (err: unknown) {
      const errorMsg = getErrorMessage(err, "Deletion failed");
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
