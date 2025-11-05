import type { AppState } from '../types';

const STORAGE_KEY = 'colpali-app-state';

/**
 * Serialize state for localStorage, excluding non-serializable data like File handles
 */
export function serializeStateForStorage(state: AppState): any {
  return {
    search: {
      query: state.search.query,
      results: state.search.results,
      hasSearched: state.search.hasSearched,
      searchDurationMs: state.search.searchDurationMs,
      k: state.search.k,
      topK: state.search.topK,
    },
    chat: {
      messages: state.chat.messages,
      imageGroups: state.chat.imageGroups,
      k: state.chat.k,
      toolCallingEnabled: state.chat.toolCallingEnabled,
      loading: false, // Don't persist loading state across sessions
      maxTokens: state.chat.maxTokens,
      reasoningEffort: state.chat.reasoningEffort,
      summaryPreference: state.chat.summaryPreference,
    },
    // Persist minimal upload state to track ongoing uploads
    upload: {
      files: null, // Never persist selected files
      fileMeta: state.upload.fileMeta,
      uploading: state.upload.uploading && !!state.upload.jobId,
      uploadProgress: state.upload.uploadProgress,
      message: state.upload.message,
      error: state.upload.error,
      jobId: state.upload.jobId,
      statusText: state.upload.statusText,
    },
    systemStatus: state.systemStatus,
  };
}

/**
 * Load state from localStorage
 */
export function loadStateFromStorage(): Partial<AppState> | null {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      return JSON.parse(stored);
    }
  } catch (error) {
    console.warn('Failed to load app state from localStorage:', error);
  }
  return null;
}

/**
 * Save state to localStorage
 */
export function saveStateToStorage(state: AppState): void {
  try {
    const serialized = serializeStateForStorage(state);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(serialized));
  } catch (error) {
    console.warn('Failed to save app state to localStorage:', error);
  }
}
