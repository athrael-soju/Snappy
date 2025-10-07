import type { AppState, AppAction } from '../types';
import { searchReducer } from './search-reducer';
import { chatReducer } from './chat-reducer';
import { uploadReducer } from './upload-reducer';
import { systemReducer } from './system-reducer';
import { globalReducer } from './global-reducer';

/**
 * Main app reducer that delegates to domain-specific reducers
 */
export function appReducer(state: AppState, action: AppAction): AppState {
  // Try each domain reducer in sequence
  const reducers = [
    searchReducer,
    chatReducer,
    uploadReducer,
    systemReducer,
    globalReducer,
  ];

  for (const reducer of reducers) {
    const result = reducer(state, action);
    if (result !== null) {
      return result;
    }
  }

  // If no reducer handled it, return state unchanged
  return state;
}
