import { useState, useEffect, useCallback, useMemo } from "react";
import { toast } from "@/components/ui/sonner";
import { zodClient } from "@/lib/api/client";
import { getErrorMessage } from "@/lib/api/errors";
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
  
  const systemStatus = state.systemStatus;

  const isReady = useMemo(() => {
    return !!(systemStatus?.collection.exists && systemStatus?.bucket.exists);
  }, [systemStatus]);

  const needsRefresh = useMemo(() => {
    if (!systemStatus?.lastChecked) return true;
    const fiveMinutes = 5 * 60 * 1000;
    return Date.now() - systemStatus.lastChecked > fiveMinutes;
  }, [systemStatus]);

  const fetchStatus = useCallback(async () => {
    setStatusLoading(true);
    try {
      const status = await zodClient.get("/status");
      setStatus(status as SystemStatus);
    } catch (err: unknown) {
      const errorMsg = getErrorMessage(err, "Failed to fetch status");
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

  return {
    systemStatus,
    setStatus,
    clearStatus,
    statusLoading,
    fetchStatus,
    isReady,
    needsRefresh,
    isSystemReady: isReady,
  };
}
