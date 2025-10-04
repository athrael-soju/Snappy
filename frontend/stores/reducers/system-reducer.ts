import type { AppState, AppAction } from '../types';

export function systemReducer(state: AppState, action: AppAction): AppState | null {
  switch (action.type) {
    case 'SYSTEM_SET_STATUS':
      return { ...state, systemStatus: action.payload };
    
    case 'SYSTEM_CLEAR_STATUS':
      return { ...state, systemStatus: null };
    
    default:
      return null;
  }
}
