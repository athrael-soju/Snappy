import type { AppState, AppAction } from '../types';
import { initialState } from '../types';

export function uploadReducer(state: AppState, action: AppAction): AppState | null {
  switch (action.type) {
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
    
    default:
      return null;
  }
}
