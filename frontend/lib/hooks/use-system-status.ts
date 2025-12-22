import { useState, useEffect, useCallback, useMemo, useRef } from "react";
import { MaintenanceService, ApiError } from "@/lib/api/generated";
import { toast } from "sonner";
import { logger } from "@/lib/utils/logger";
import type { SystemStatus } from "@/stores/types";
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

  const collectionReady = !!systemStatus?.collection.exists;
  const bucketReady = !!systemStatus?.bucket.exists;

  const isReady = useMemo(() => {
    return collectionReady && bucketReady;
  }, [collectionReady, bucketReady]);

  const canReset = useMemo(() => {
    return collectionReady && bucketReady;
  }, [collectionReady, bucketReady]);

  const needsRefresh = useMemo(() => {
    if (!systemStatus?.lastChecked) return true;
    const fiveMinutes = 5 * 60 * 1000;
    return Date.now() - systemStatus.lastChecked > fiveMinutes;
  }, [systemStatus]);

  const fetchStatus = useCallback(async () => {
    setStatusLoading(true);
    try {
      const status = await MaintenanceService.getStatusStatusGet();
      setStatus(status as SystemStatus);
    } catch (err: unknown) {
      let errorMsg = "Failed to fetch status";
      if (err instanceof ApiError) {
        errorMsg = `${err.status}: ${err.message}`;
        logger.error('System status fetch failed', { error: err, status: err.status });
      } else if (err instanceof Error) {
        errorMsg = err.message;
        logger.error('System status fetch failed', { error: err });
      }
      toast.error("Status Check Failed", { description: errorMsg });
    } finally {
      setStatusLoading(false);
    }
  }, [setStatus]);

  // Store fetchStatus in a ref to prevent event listener from re-registering
  const fetchStatusRef = useRef(fetchStatus);
  useEffect(() => {
    fetchStatusRef.current = fetchStatus;
  }, [fetchStatus]);

  // Fetch status on mount
  useEffect(() => {
    fetchStatus();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Only run on mount

  // Listen for system status change events (one-time registration)
  useEffect(() => {
    const handler = () => {
      fetchStatusRef.current();
    };
    window.addEventListener('systemStatusChanged', handler);
    return () => window.removeEventListener('systemStatusChanged', handler);
  }, []); // Empty deps - register once, use ref for latest function

  return {
    systemStatus,
    setStatus,
    clearStatus,
    statusLoading,
    fetchStatus,
    isReady,
    needsRefresh,
    isSystemReady: isReady,
    canReset,
  };
}
