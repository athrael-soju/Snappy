import type { AppState, AppAction } from '../types';

export function globalReducer(state: AppState, action: AppAction): AppState | null {
  switch (action.type) {
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

    case 'SET_ANIMATED_BACKGROUND':
      return {
        ...state,
        preferences: {
          ...state.preferences,
          animatedBackground: action.payload,
        },
      };
    
    default:
      return null;
  }
}
