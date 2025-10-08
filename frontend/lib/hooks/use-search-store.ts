import { useAppStore } from '@/stores/app-store';
import type { SearchItem } from "@/lib/api/runtime";

/**
 * Hook for accessing and managing search state
 */
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
    setTopK: (topK: number) => dispatch({ type: 'SEARCH_SET_TOP_K', payload: topK }),
    reset: () => dispatch({ type: 'SEARCH_RESET' }),
  };
}
