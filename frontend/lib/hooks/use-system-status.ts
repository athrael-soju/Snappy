import { useState, useEffect, useCallback } from "react";
import { MaintenanceService, ApiError } from "@/lib/api/generated";
import { toast } from "@/components/ui/sonner";
import type { SystemStatus } from "@/components/maintenance/types";
import { useAppStore } from "@/stores/app-store";

/**
 * Hook to manage system status (collection and bucket health)
 */
export function useSystemStatus() {
  const [statusLoading, setStatusLoading] = useState(false);
  const { state, dispatch } = useAppStore();

  const setStatus = useCallback((status: SystemStatus) => {
    dispatch({ type: 'SYSTEM_SET_STATUS', payload: { ...status, lastChecked: Date.now() } });
  }, [dispatch]);
  
  const clearStatus = useCallback(() => {
    dispatch({ type: 'SYSTEM_CLEAR_STATUS' });
  }, [dispatch]);
  
  const isReady = useCallback(() => {
    return !!(state.systemStatus?.collection.exists && state.systemStatus?.bucket.exists);
  }, [state.systemStatus]);
  
  const needsRefresh = useCallback(() => {
    if (!state.systemStatus?.lastChecked) return true;
    const fiveMinutes = 5 * 60 * 1000;
    return Date.now() - state.systemStatus.lastChecked > fiveMinutes;
  }, [state.systemStatus]);

  const fetchStatus = useCallback(async () => {
    setStatusLoading(true);
    try {
      const status = await MaintenanceService.getStatusStatusGet();
      setStatus(status as SystemStatus);
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
  }, [setStatus]);

  useEffect(() => {
    fetchStatus();
  }, [fetchStatus]);

  useEffect(() => {
    const handler = () => fetchStatus();
    window.addEventListener('systemStatusChanged', handler);
    return () => window.removeEventListener('systemStatusChanged', handler);
  }, [fetchStatus]);

  const systemStatus = state.systemStatus;
  const isSystemReady = !!(systemStatus?.collection.exists && systemStatus?.bucket.exists);

  return {
    systemStatus,
    setStatus,
    clearStatus,
    statusLoading,
    fetchStatus,
    isReady: isReady(),
    needsRefresh: needsRefresh(),
    isSystemReady,
  };
}
