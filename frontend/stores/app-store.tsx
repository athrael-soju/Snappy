"use client";

import React, { createContext, useContext, useReducer, useEffect, ReactNode } from 'react';
import { appReducer } from './reducers';
import { initialState } from './types';
import { loadStateFromStorage, saveStateToStorage } from './utils/storage';
import { useUploadSSE } from '../lib/hooks/use-upload-sse';
import type { AppState, AppAction } from './types';

const SUCCESS_MESSAGE_DISMISS_MS = 4500;
const ERROR_MESSAGE_DISMISS_MS = 6000;

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

  useEffect(() => {
    if (!state.upload.message || state.upload.uploading) {
      return;
    }

    const timeoutId = setTimeout(() => {
      dispatch({ type: 'UPLOAD_SET_MESSAGE', payload: null });
    }, SUCCESS_MESSAGE_DISMISS_MS);

    return () => clearTimeout(timeoutId);
  }, [state.upload.message, state.upload.uploading, dispatch]);

  useEffect(() => {
    if (!state.upload.error || state.upload.uploading) {
      return;
    }

    const timeoutId = setTimeout(() => {
      dispatch({ type: 'UPLOAD_SET_ERROR', payload: null });
    }, ERROR_MESSAGE_DISMISS_MS);

    return () => clearTimeout(timeoutId);
  }, [state.upload.error, state.upload.uploading, dispatch]);

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
