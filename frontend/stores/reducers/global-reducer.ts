import type { AppState, AppAction } from '../types';

export function globalReducer(state: AppState, action: AppAction): AppState | null {
  switch (action.type) {
    case 'HYDRATE_FROM_STORAGE': {
      const payload = action.payload;
      if (!payload || Object.keys(payload).length === 0) {
        return { ...state };
      }

      const nextState: AppState = { ...state };

      if (payload.search) {
        nextState.search = { ...state.search, ...payload.search };
      }

      if (payload.chat) {
        nextState.chat = { ...state.chat, ...payload.chat };
      }

      if (payload.upload) {
        const mergedUpload = { ...state.upload, ...payload.upload };
        if (mergedUpload.uploading && !mergedUpload.jobId) {
          mergedUpload.uploading = false;
          mergedUpload.uploadProgress = 0;
          mergedUpload.statusText = null;
          mergedUpload.message = null;
          mergedUpload.error = null;
        }
        nextState.upload = mergedUpload;
      }

      if (payload.systemStatus !== undefined) {
        nextState.systemStatus = payload.systemStatus ?? null;
      }

      if (payload.lastVisited) {
        nextState.lastVisited = { ...state.lastVisited, ...payload.lastVisited };
      }

      return nextState;
    }

    case 'SET_PAGE_VISITED':
      return {
        ...state,
        lastVisited: {
          ...state.lastVisited,
          [action.payload.page]: action.payload.timestamp,
        },
      };

    default:
      return null;
  }
}
