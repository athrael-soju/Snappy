import { useState, useEffect, useCallback } from "react";
import { MaintenanceService, ApiError } from "@/lib/api/generated";
import { toast } from "@/components/ui/sonner";
import type { SystemStatus } from "@/components/maintenance/types";
import { useAppStore } from "@/stores/app-store";

/**
 * Hook to manage system status (collection and bucket health)
 */
export function useSystemStatus() {
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);
  const [statusLoading, setStatusLoading] = useState(false);
  const { state, dispatch } = useAppStore();

  const setStatus = (status: SystemStatus) => {
    dispatch({ type: 'SYSTEM_SET_STATUS', payload: { ...status, lastChecked: Date.now() } });
  };
  
  const clearStatus = () => {
    dispatch({ type: 'SYSTEM_CLEAR_STATUS' });
  };
  
  const isReady = () => {
    return state.systemStatus?.collection.exists && state.systemStatus?.bucket.exists;
  };
  
  const needsRefresh = () => {
    if (!state.systemStatus?.lastChecked) return true;
    const fiveMinutes = 5 * 60 * 1000;
    return Date.now() - state.systemStatus.lastChecked > fiveMinutes;
  };

  const fetchStatus = useCallback(async () => {
    setStatusLoading(true);
    try {
      const status = await MaintenanceService.getStatusStatusGet();
      setSystemStatus(status as SystemStatus);
    } catch (err: unknown) {
      let errorMsg = "Failed to fetch status";
      if (err instanceof ApiError) {
        errorMsg = `${err.status}: ${err.message}`;
      } else if (err instanceof Error) {
        errorMsg = err.message;
      }
      toast.error("Status Check Failed", { description: errorMsg });
    } finally {
      setStatusLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStatus();
  }, [fetchStatus]);

  const isSystemReady = systemStatus?.collection.exists && systemStatus?.bucket.exists;

  return {
    systemStatus: state.systemStatus,
    setStatus,
    clearStatus,
    statusLoading,
    fetchStatus,
    isReady: isReady(),
    needsRefresh: needsRefresh(),
    isSystemReady : !!isSystemReady,
  };
}
