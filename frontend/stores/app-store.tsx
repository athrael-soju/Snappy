"use client";

import "@/lib/api/client";
import React, { createContext, useContext, useReducer, useEffect, ReactNode } from 'react';
import { appReducer } from './reducers';
import { initialState } from './types';
import { loadStateFromStorage, saveStateToStorage } from './utils/storage';
import { useUploadSSE } from '../lib/hooks/use-upload-sse';
import type { AppState, AppAction } from './types';

// Re-export types for convenience
export type { 
  AppState, 
  AppAction, 
  SearchState, 
  ChatState, 
  UploadState, 
  SystemStatus 
} from './types';

// Context
const AppContext = createContext<{
  state: AppState;
  dispatch: React.Dispatch<AppAction>;
} | null>(null);

// Provider component
export function AppStoreProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(appReducer, initialState);

  // Hydrate from localStorage on mount
  useEffect(() => {
    const stored = loadStateFromStorage();
    if (stored) {
      dispatch({ type: 'HYDRATE_FROM_STORAGE', payload: stored });
    }
  }, []);

  // Use SSE hook for upload progress tracking
  useUploadSSE({ uploadState: state.upload, dispatch });

  // Persist to localStorage when state changes (debounced)
  useEffect(() => {
    const timeoutId = setTimeout(() => {
      saveStateToStorage(state);
    }, 500); // Debounce to avoid excessive localStorage writes

    return () => clearTimeout(timeoutId);
  }, [state]);

  return (
    <AppContext.Provider value={{ state, dispatch }}>
      {children}
    </AppContext.Provider>
  );
}

// Hook to use the app store
export function useAppStore() {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useAppStore must be used within an AppStoreProvider');
  }
  return context;
}

// Re-export domain-specific hooks
export { useSearchStore } from '../lib/hooks/use-search-store';
export { useChatStore } from '../lib/hooks/use-chat-store';
export { useUploadStore } from '../lib/hooks/use-upload-store';
export { useSystemStatus } from '../lib/hooks/use-system-status';
