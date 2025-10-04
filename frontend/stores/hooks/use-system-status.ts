import { useAppStore } from '../app-store';
import type { SystemStatus } from '../types';

/**
 * Hook for accessing and managing system status
 */
export function useSystemStatus() {
  const { state, dispatch } = useAppStore();
  
  const setStatus = (status: SystemStatus) => {
    dispatch({ type: 'SYSTEM_SET_STATUS', payload: status });
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
  
  return {
    systemStatus: state.systemStatus,
    setStatus,
    clearStatus,
    isReady: isReady(),
    needsRefresh: needsRefresh(),
  };
}
