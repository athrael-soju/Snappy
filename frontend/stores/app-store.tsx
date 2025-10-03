"use client";

import React, { createContext, useContext, useReducer, useEffect, useRef, useCallback, ReactNode } from 'react';
import type { SearchItem } from "@/lib/api/generated";
import type { ChatMessage } from "@/lib/hooks/use-chat";
import { toast } from '@/components/ui/sonner';

// Types for our app state
export interface SearchState {
  query: string;
  results: SearchItem[];
  hasSearched: boolean;
  searchDurationMs: number | null;
  k: number;
}

export interface ChatState {
  messages: ChatMessage[];
  imageGroups: Array<{ url: string | null; label: string | null; score: number | null }>[];
  k: number;
  toolCallingEnabled: boolean;
  loading: boolean;
}

export interface UploadState {
  files: FileList | null;
  uploading: boolean;
  uploadProgress: number;
  message: string | null;
  error: string | null;
  jobId: string | null;
  statusText: string | null;
}

export interface AppState {
  search: SearchState;
  chat: ChatState;
  upload: UploadState;
  lastVisited: {
    search: number | null;
    chat: number | null;
    upload: number | null;
  };
}

// Action types
type AppAction =
  // Search actions
  | { type: 'SEARCH_SET_QUERY'; payload: string }
  | { type: 'SEARCH_SET_RESULTS'; payload: { results: SearchItem[]; duration: number | null } }
  | { type: 'SEARCH_SET_HAS_SEARCHED'; payload: boolean }
  | { type: 'SEARCH_SET_K'; payload: number }
  | { type: 'SEARCH_RESET' }
  
  // Chat actions
  | { type: 'CHAT_SET_MESSAGES'; payload: ChatMessage[] }
  | { type: 'CHAT_ADD_MESSAGE'; payload: ChatMessage }
  | { type: 'CHAT_UPDATE_LAST_MESSAGE'; payload: string }
  | { type: 'CHAT_UPDATE_MESSAGE_CITATIONS'; payload: { messageId: string; citations: Array<{ url: string | null; label: string | null; score: number | null }> } }
  | { type: 'CHAT_SET_IMAGE_GROUPS'; payload: Array<{ url: string | null; label: string | null; score: number | null }>[] }
  | { type: 'CHAT_SET_K'; payload: number }
  | { type: 'CHAT_SET_TOOL_CALLING'; payload: boolean }
  | { type: 'CHAT_SET_LOADING'; payload: boolean }
  | { type: 'CHAT_RESET' }
  
  // Upload actions
  | { type: 'UPLOAD_SET_FILES'; payload: FileList | null }
  | { type: 'UPLOAD_SET_UPLOADING'; payload: boolean }
  | { type: 'UPLOAD_SET_PROGRESS'; payload: number }
  | { type: 'UPLOAD_SET_MESSAGE'; payload: string | null }
  | { type: 'UPLOAD_SET_ERROR'; payload: string | null }
  | { type: 'UPLOAD_SET_JOB_ID'; payload: string | null }
  | { type: 'UPLOAD_SET_STATUS_TEXT'; payload: string | null }
  | { type: 'UPLOAD_RESET' }
  
  // Global actions
  | { type: 'HYDRATE_FROM_STORAGE'; payload: Partial<AppState> }
  | { type: 'SET_PAGE_VISITED'; payload: { page: 'search' | 'chat' | 'upload'; timestamp: number } };

// Initial state
const initialState: AppState = {
  search: {
    query: '',
    results: [],
    hasSearched: false,
    searchDurationMs: null,
    k: 5,
  },
  chat: {
    messages: [],
    imageGroups: [],
    k: 5,
    toolCallingEnabled: true,
    loading: false,
  },
  upload: {
    files: null,
    uploading: false,
    uploadProgress: 0,
    message: null,
    error: null,
    jobId: null,
    statusText: null,
  },
  lastVisited: {
    search: null,
    chat: null,
    upload: null,
  },
};

// Reducer function
function appReducer(state: AppState, action: AppAction): AppState {
  switch (action.type) {
    // Search actions
    case 'SEARCH_SET_QUERY':
      return { ...state, search: { ...state.search, query: action.payload } };
    case 'SEARCH_SET_RESULTS':
      return { 
        ...state, 
        search: { 
          ...state.search, 
          results: action.payload.results,
          searchDurationMs: action.payload.duration,
          hasSearched: true 
        } 
      };
    case 'SEARCH_SET_HAS_SEARCHED':
      return { ...state, search: { ...state.search, hasSearched: action.payload } };
    case 'SEARCH_SET_K':
      return { ...state, search: { ...state.search, k: action.payload } };
    case 'SEARCH_RESET':
      return { ...state, search: initialState.search };

    // Chat actions
    case 'CHAT_SET_MESSAGES':
      return { ...state, chat: { ...state.chat, messages: action.payload } };
    case 'CHAT_ADD_MESSAGE':
      return { ...state, chat: { ...state.chat, messages: [...state.chat.messages, action.payload] } };
    case 'CHAT_UPDATE_LAST_MESSAGE':
      return {
        ...state,
        chat: {
          ...state.chat,
          messages: state.chat.messages.map((msg, idx) =>
            idx === state.chat.messages.length - 1 ? { ...msg, content: action.payload } : msg
          ),
        },
      };
    case 'CHAT_UPDATE_MESSAGE_CITATIONS':
      return {
        ...state,
        chat: {
          ...state.chat,
          messages: state.chat.messages.map((msg) =>
            msg.id === action.payload.messageId ? { ...msg, citations: action.payload.citations } : msg
          ),
        },
      };
    case 'CHAT_SET_IMAGE_GROUPS':
      return { ...state, chat: { ...state.chat, imageGroups: action.payload } };
    case 'CHAT_SET_K':
      return { ...state, chat: { ...state.chat, k: action.payload } };
    case 'CHAT_SET_TOOL_CALLING':
      return { ...state, chat: { ...state.chat, toolCallingEnabled: action.payload } };
    case 'CHAT_SET_LOADING':
      return { ...state, chat: { ...state.chat, loading: action.payload } };
    case 'CHAT_RESET':
      // Preserve user settings when clearing conversation
      return { 
        ...state, 
        chat: { 
          ...initialState.chat,
          k: state.chat.k, // Preserve k setting
          toolCallingEnabled: state.chat.toolCallingEnabled, // Preserve tool calling setting
        } 
      };

    // Upload actions
    case 'UPLOAD_SET_FILES':
      return { ...state, upload: { ...state.upload, files: action.payload } };
    case 'UPLOAD_SET_UPLOADING':
      return { ...state, upload: { ...state.upload, uploading: action.payload } };
    case 'UPLOAD_SET_PROGRESS':
      return { ...state, upload: { ...state.upload, uploadProgress: action.payload } };
    case 'UPLOAD_SET_MESSAGE':
      return { ...state, upload: { ...state.upload, message: action.payload } };
    case 'UPLOAD_SET_ERROR':
      return { ...state, upload: { ...state.upload, error: action.payload } };
    case 'UPLOAD_SET_JOB_ID':
      return { ...state, upload: { ...state.upload, jobId: action.payload } };
    case 'UPLOAD_SET_STATUS_TEXT':
      return { ...state, upload: { ...state.upload, statusText: action.payload } };
    case 'UPLOAD_RESET':
      return { ...state, upload: initialState.upload };

    // Global actions
    case 'HYDRATE_FROM_STORAGE':
      return { ...state, ...action.payload };
    case 'SET_PAGE_VISITED':
      return {
        ...state,
        lastVisited: {
          ...state.lastVisited,
          [action.payload.page]: action.payload.timestamp,
        },
      };

    default:
      return state;
  }
}

// Context
const AppContext = createContext<{
  state: AppState;
  dispatch: React.Dispatch<AppAction>;
} | null>(null);

// Helper to serialize state for localStorage (excluding non-serializable data like FileList)
function serializeStateForStorage(state: AppState): any {
  return {
    search: {
      query: state.search.query,
      results: state.search.results,
      hasSearched: state.search.hasSearched,
      searchDurationMs: state.search.searchDurationMs,
      k: state.search.k,
    },
    chat: {
      messages: state.chat.messages,
      imageGroups: state.chat.imageGroups,
      k: state.chat.k,
      toolCallingEnabled: state.chat.toolCallingEnabled,
      loading: false, // Don't persist loading state across sessions
    },
    // Persist minimal upload state to track ongoing uploads
    upload: {
      files: null, // Never persist FileList
      uploading: state.upload.uploading,
      uploadProgress: state.upload.uploadProgress,
      message: state.upload.message,
      error: state.upload.error,
      jobId: state.upload.jobId,
      statusText: state.upload.statusText,
    },
  };
}

// Provider component
export function AppStoreProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(appReducer, initialState);
  const eventSourceRef = useRef<EventSource | null>(null);

  // Function to properly close existing SSE connection
  const closeSSEConnection = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
  }, []);

  // Hydrate from localStorage on mount
  useEffect(() => {
    try {
      const stored = localStorage.getItem('colpali-app-state');
      if (stored) {
        const parsed = JSON.parse(stored);
        dispatch({ type: 'HYDRATE_FROM_STORAGE', payload: parsed });
      }
    } catch (error) {
      console.warn('Failed to load app state from localStorage:', error);
    }
  }, []);

  // Global SSE connection management for uploads
  useEffect(() => {
    // Only connect if we have an ongoing upload with a valid job ID
    if (!state.upload.jobId || !state.upload.uploading) {
      closeSSEConnection();
      return;
    }

    // Don't create multiple connections
    if (eventSourceRef.current) {
      return;
    }
   
    const es = new EventSource(`${process.env.NEXT_PUBLIC_API_BASE_URL || ''}/progress/stream/${state.upload.jobId}`);
    eventSourceRef.current = es;

    es.addEventListener('progress', (ev: MessageEvent) => {
      try {
        const data = JSON.parse(ev.data || '{}');
        const pct = Number(data.percent ?? 0);
        dispatch({ type: 'UPLOAD_SET_PROGRESS', payload: pct });
        if (data.message) {
          dispatch({ type: 'UPLOAD_SET_STATUS_TEXT', payload: data.message });
        }

        if (data.status === 'completed') {
          closeSSEConnection();
          dispatch({ type: 'UPLOAD_SET_PROGRESS', payload: 100 });
          const successMsg = data.message || `Upload completed`;
          dispatch({ type: 'UPLOAD_SET_MESSAGE', payload: successMsg });
          dispatch({ type: 'UPLOAD_SET_UPLOADING', payload: false });
          dispatch({ type: 'UPLOAD_SET_JOB_ID', payload: null });
          dispatch({ type: 'UPLOAD_SET_FILES', payload: null }); // Clear files on completion
          
          // Show toast notification
          if (typeof window !== 'undefined') {
            toast.success('Upload Complete', { description: successMsg });
          }
        } else if (data.status === 'failed') {
          closeSSEConnection();
          const errMsg = data.error || 'Upload failed';
          dispatch({ type: 'UPLOAD_SET_ERROR', payload: errMsg });
          dispatch({ type: 'UPLOAD_SET_UPLOADING', payload: false });
          dispatch({ type: 'UPLOAD_SET_JOB_ID', payload: null });
          
          // Show toast notification
          if (typeof window !== 'undefined') {
            toast.error('Upload Failed', { description: errMsg });
          }
        } else if (data.status === 'cancelled') {
          closeSSEConnection();
          const cancelMsg = data.message || 'Upload cancelled';
          dispatch({ type: 'UPLOAD_SET_MESSAGE', payload: cancelMsg });
          dispatch({ type: 'UPLOAD_SET_UPLOADING', payload: false });
          dispatch({ type: 'UPLOAD_SET_JOB_ID', payload: null });
          dispatch({ type: 'UPLOAD_SET_FILES', payload: null });
          
          // Show toast notification
          if (typeof window !== 'undefined') {
            toast.info('Upload Cancelled', { description: cancelMsg });
          }
        }
      } catch (e) {
        console.warn('Failed to parse SSE data:', e);
      }
    });

    es.addEventListener('not_found', () => {
      closeSSEConnection();
      dispatch({ type: 'UPLOAD_SET_ERROR', payload: 'Upload job not found. It may have completed or failed.' });
      dispatch({ type: 'UPLOAD_SET_UPLOADING', payload: false });
      dispatch({ type: 'UPLOAD_SET_JOB_ID', payload: null });
      dispatch({ type: 'UPLOAD_SET_PROGRESS', payload: 0 });
    });

    es.addEventListener('error', (e) => {
      console.warn('Global SSE connection error:', e);
      // Don't immediately fail, let EventSource handle retries
    });

    return () => {
      closeSSEConnection();
    };
  }, [state.upload.jobId, state.upload.uploading, closeSSEConnection]);

  // Cleanup SSE connection on unmount
  useEffect(() => {
    return () => {
      closeSSEConnection();
    };
  }, [closeSSEConnection]);

  // Persist to localStorage when state changes (debounced)
  useEffect(() => {
    const timeoutId = setTimeout(() => {
      try {
        const serialized = serializeStateForStorage(state);
        localStorage.setItem('colpali-app-state', JSON.stringify(serialized));
      } catch (error) {
        console.warn('Failed to save app state to localStorage:', error);
      }
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

// Convenience hooks for specific parts of the state
export function useSearchStore() {
  const { state, dispatch } = useAppStore();
  return {
    ...state.search,
    setQuery: (query: string) => dispatch({ type: 'SEARCH_SET_QUERY', payload: query }),
    setResults: (results: SearchItem[], duration: number | null) => 
      dispatch({ type: 'SEARCH_SET_RESULTS', payload: { results, duration } }),
    setHasSearched: (hasSearched: boolean) => 
      dispatch({ type: 'SEARCH_SET_HAS_SEARCHED', payload: hasSearched }),
    setK: (k: number) => dispatch({ type: 'SEARCH_SET_K', payload: k }),
    reset: () => dispatch({ type: 'SEARCH_RESET' }),
  };
}

export function useChatStore() {
  const { state, dispatch } = useAppStore();
  return {
    ...state.chat,
    setMessages: (messages: ChatMessage[]) => 
      dispatch({ type: 'CHAT_SET_MESSAGES', payload: messages }),
    addMessage: (message: ChatMessage) => 
      dispatch({ type: 'CHAT_ADD_MESSAGE', payload: message }),
    updateLastMessage: (content: string) => 
      dispatch({ type: 'CHAT_UPDATE_LAST_MESSAGE', payload: content }),
    updateMessageCitations: (messageId: string, citations: Array<{ url: string | null; label: string | null; score: number | null }>) => 
      dispatch({ type: 'CHAT_UPDATE_MESSAGE_CITATIONS', payload: { messageId, citations } }),
    setImageGroups: (imageGroups: Array<{ url: string | null; label: string | null; score: number | null }>[]) => 
      dispatch({ type: 'CHAT_SET_IMAGE_GROUPS', payload: imageGroups }),
    setK: (k: number) => dispatch({ type: 'CHAT_SET_K', payload: k }),
    setToolCallingEnabled: (enabled: boolean) => 
      dispatch({ type: 'CHAT_SET_TOOL_CALLING', payload: enabled }),
    setLoading: (loading: boolean) => 
      dispatch({ type: 'CHAT_SET_LOADING', payload: loading }),
    reset: () => dispatch({ type: 'CHAT_RESET' }),
  };
}

export function useUploadStore() {
  const { state, dispatch } = useAppStore();
  
  const cancelUpload = async () => {
    const jobId = state.upload.jobId;
    if (!jobId) return;
    
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL || ''}/index/cancel/${jobId}`, {
        method: 'POST',
      });
      
      if (!response.ok) {
        throw new Error(`Failed to cancel: ${response.statusText}`);
      }      
    } catch (error) {
      console.error('Failed to cancel upload:', error);
      toast.error('Cancellation Failed', { 
        description: error instanceof Error ? error.message : 'Could not cancel upload' 
      });
    }
  };
  
  return {
    ...state.upload,
    setFiles: (files: FileList | null) => 
      dispatch({ type: 'UPLOAD_SET_FILES', payload: files }),
    setUploading: (uploading: boolean) => 
      dispatch({ type: 'UPLOAD_SET_UPLOADING', payload: uploading }),
    setProgress: (progress: number) => 
      dispatch({ type: 'UPLOAD_SET_PROGRESS', payload: progress }),
    setMessage: (message: string | null) => 
      dispatch({ type: 'UPLOAD_SET_MESSAGE', payload: message }),
    setError: (error: string | null) => 
      dispatch({ type: 'UPLOAD_SET_ERROR', payload: error }),
    setJobId: (jobId: string | null) => 
      dispatch({ type: 'UPLOAD_SET_JOB_ID', payload: jobId }),
    setStatusText: (statusText: string | null) => 
      dispatch({ type: 'UPLOAD_SET_STATUS_TEXT', payload: statusText }),
    reset: () => dispatch({ type: 'UPLOAD_RESET' }),
    cancelUpload,
  };
}
