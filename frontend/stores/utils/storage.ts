import type { AppState } from "../types";

const STORAGE_KEY = "colpali-app-state";

function getLocalStorage(): Storage | null {
  if (typeof window === "undefined") {
    return null;
  }

  try {
    return window.localStorage;
  } catch (error) {
    console.warn("Unable to access localStorage:", error);
    return null;
  }
}

/**
 * Safely read a raw string value from localStorage.
 */
export function readStorageValue(key: string): string | null {
  const storage = getLocalStorage();
  if (!storage) return null;

  try {
    return storage.getItem(key);
  } catch (error) {
    console.warn(`Failed to read "${key}" from localStorage:`, error);
    return null;
  }
}

/**
 * Safely write a raw string value to localStorage.
 */
export function writeStorageValue(key: string, value: string): boolean {
  const storage = getLocalStorage();
  if (!storage) return false;

  try {
    storage.setItem(key, value);
    return true;
  } catch (error) {
    console.warn(`Failed to write "${key}" to localStorage:`, error);
    return false;
  }
}

/**
 * Remove a key from localStorage.
 */
export function removeStorageValue(key: string): boolean {
  const storage = getLocalStorage();
  if (!storage) return false;

  try {
    storage.removeItem(key);
    return true;
  } catch (error) {
    console.warn(`Failed to remove "${key}" from localStorage:`, error);
    return false;
  }
}

/**
 * Read a JSON value from localStorage.
 */
export function readJSONStorageValue<T>(key: string, fallback: T | null = null): T | null {
  const raw = readStorageValue(key);
  if (raw === null) return fallback;

  try {
    return JSON.parse(raw) as T;
  } catch (error) {
    console.warn(`Failed to parse JSON for "${key}" from localStorage:`, error);
    return fallback;
  }
}

/**
 * Write a JSON value to localStorage.
 */
export function writeJSONStorageValue<T>(key: string, value: T): boolean {
  return writeStorageValue(key, JSON.stringify(value));
}

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
    },
    // Persist minimal upload state to track ongoing uploads
    upload: {
      files: null, // Never persist selected files
      fileMeta: state.upload.fileMeta,
      uploading: state.upload.uploading,
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
  return readJSONStorageValue<Partial<AppState>>(STORAGE_KEY);
}

/**
 * Save state to localStorage
 */
export function saveStateToStorage(state: AppState): void {
  const serialized = serializeStateForStorage(state);
  if (!writeJSONStorageValue(STORAGE_KEY, serialized)) {
    console.warn("Failed to save app state to localStorage");
  }
}
