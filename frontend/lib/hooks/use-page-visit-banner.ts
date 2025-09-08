"use client";

import { useEffect, useState } from "react";
import { useAppStore } from "@/stores/app-store";

export function usePageVisitBanner(
  page: 'search' | 'chat' | 'upload',
  hasData: boolean,
  dependencies: any[] = []
) {
  const { state, dispatch } = useAppStore();
  const [showBanner, setShowBanner] = useState(false);

  useEffect(() => {
    const currentTime = Date.now();
    const lastVisited = state.lastVisited[page];
    
    // Show banner if:
    // 1. We have data to restore
    // 2. This isn't the first visit (lastVisited exists)
    // 3. We haven't shown the banner for this session yet
    if (hasData && lastVisited && currentTime - lastVisited > 1000) {
      setShowBanner(true);
    }

    // Record this visit
    dispatch({
      type: 'SET_PAGE_VISITED',
      payload: { page, timestamp: currentTime }
    });
  }, dependencies);

  return {
    showBanner,
    hideBanner: () => setShowBanner(false),
  };
}
