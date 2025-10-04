import type { AppState, AppAction } from '../types';
import { initialState } from '../types';

export function searchReducer(state: AppState, action: AppAction): AppState | null {
  switch (action.type) {
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
    
    case 'SEARCH_SET_TOP_K':
      return { ...state, search: { ...state.search, topK: action.payload } };
    
    case 'SEARCH_RESET':
      return { ...state, search: initialState.search };
    
    default:
      return null;
  }
}
