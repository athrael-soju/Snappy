import type { SearchItem } from "@/lib/api/generated/models/SearchItem";
import type { ChatMessage } from "@/lib/hooks/use-chat";

// State Types
export interface SearchState {
  query: string;
  results: SearchItem[];
  hasSearched: boolean;
  searchDurationMs: number | null;
  k: number;
  topK: number;
}

export interface ChatState {
  messages: ChatMessage[];
  imageGroups: Array<{ url: string | null; label: string | null; score: number | null }>[];
  k: number;
  toolCallingEnabled: boolean;
  loading: boolean;
  reasoningEffort: 'minimal' | 'low' | 'medium' | 'high';
  summaryPreference: 'auto' | 'concise' | 'detailed' | null;
}

export interface UploadFileMeta {
  name: string;
  size: number;
  type: string;
  lastModified?: number;
}

export interface UploadState {
  files: File[] | null;
  fileMeta: UploadFileMeta[] | null;
  uploading: boolean;
  uploadProgress: number;
  message: string | null;
  error: string | null;
  jobId: string | null;
  statusText: string | null;
  // OCR state (separate from indexing)
  ocrJobId: string | null;
  ocrProgress: number;
  ocrStatusText: string | null;
  ocrError: string | null;
  uploadedFilenames: string[] | null; // Track filenames for OCR processing
}

export interface SystemStatus {
  collection: {
    name: string;
    exists: boolean;
    vector_count: number;
    unique_files: number;
    error: string | null;
    embedded?: boolean;
    image_store_mode?: "inline" | "minio" | string;
    size_mb?: number;
  };
  bucket: {
    name: string;
    exists: boolean;
    object_count: number;
    page_count?: number;
    element_count?: number;
    size_mb?: number;
    error: string | null;
  };
  duckdb?: {
    name: string;
    enabled: boolean;
    available: boolean;
    page_count: number;
    region_count: number;
    database_size_mb: number;
    error: string | null;
  };
  lastChecked: number | null;
}

export interface AppState {
  search: SearchState;
  chat: ChatState;
  upload: UploadState;
  systemStatus: SystemStatus | null;
  lastVisited: {
    search: number | null;
    chat: number | null;
    upload: number | null;
  };
}

// Action Types
export type AppAction =
  // Search actions
  | { type: 'SEARCH_SET_QUERY'; payload: string }
  | { type: 'SEARCH_SET_RESULTS'; payload: { results: SearchItem[]; duration: number | null } }
  | { type: 'SEARCH_SET_HAS_SEARCHED'; payload: boolean }
  | { type: 'SEARCH_SET_K'; payload: number }
  | { type: 'SEARCH_SET_TOP_K'; payload: number }
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
  | { type: 'CHAT_SET_REASONING_EFFORT'; payload: 'minimal' | 'low' | 'medium' | 'high' }
  | { type: 'CHAT_SET_SUMMARY_PREFERENCE'; payload: 'auto' | 'concise' | 'detailed' | null }
  | { type: 'CHAT_REMOVE_EMPTY_ASSISTANT' }
  | { type: 'CHAT_RESET' }

  // Upload actions
  | { type: 'UPLOAD_SET_FILES'; payload: File[] | null }
  | { type: 'UPLOAD_SET_FILE_META'; payload: UploadFileMeta[] | null }
  | { type: 'UPLOAD_SET_UPLOADING'; payload: boolean }
  | { type: 'UPLOAD_SET_PROGRESS'; payload: number }
  | { type: 'UPLOAD_SET_MESSAGE'; payload: string | null }
  | { type: 'UPLOAD_SET_ERROR'; payload: string | null }
  | { type: 'UPLOAD_SET_JOB_ID'; payload: string | null }
  | { type: 'UPLOAD_SET_STATUS_TEXT'; payload: string | null }
  | { type: 'UPLOAD_SET_UPLOADED_FILENAMES'; payload: string[] | null }
  // OCR actions
  | { type: 'UPLOAD_SET_OCR_JOB_ID'; payload: string | null }
  | { type: 'UPLOAD_SET_OCR_PROGRESS'; payload: number }
  | { type: 'UPLOAD_SET_OCR_STATUS_TEXT'; payload: string | null }
  | { type: 'UPLOAD_SET_OCR_ERROR'; payload: string | null }
  | { type: 'UPLOAD_RESET' }

  // System status actions
  | { type: 'SYSTEM_SET_STATUS'; payload: SystemStatus }
  | { type: 'SYSTEM_CLEAR_STATUS' }

  // Global actions
  | { type: 'HYDRATE_FROM_STORAGE'; payload: Partial<AppState> }
  | { type: 'SET_PAGE_VISITED'; payload: { page: 'search' | 'chat' | 'upload'; timestamp: number } };

// Initial State
export const initialState: AppState = {
  search: {
    query: '',
    results: [],
    hasSearched: false,
    searchDurationMs: null,
    k: 5,
    topK: 16,
  },
  chat: {
    messages: [],
    imageGroups: [],
    k: 5,
    toolCallingEnabled: true,
    loading: false,
    reasoningEffort: 'minimal',
    summaryPreference: null,
  },
  upload: {
    files: null,
    fileMeta: null,
    uploading: false,
    uploadProgress: 0,
    message: null,
    error: null,
    jobId: null,
    statusText: null,
    ocrJobId: null,
    ocrProgress: 0,
    ocrStatusText: null,
    ocrError: null,
    uploadedFilenames: null,
  },
  systemStatus: null,
  lastVisited: {
    search: null,
    chat: null,
    upload: null,
  },
};
