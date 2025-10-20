"use client";

import { useCallback, useState } from "react";

import { SystemStatusActions } from "@/components/system-status-actions";
import { useSystemStatus } from "@/stores/app-store";

export function SystemStatusFloating() {
  const { isReady, statusLoading, fetchStatus, needsRefresh } = useSystemStatus();
  const [dismissed, setDismissed] = useState(false);

  const handleRefresh = useCallback(() => {
    void fetchStatus();
    if (dismissed) {
      setDismissed(false);
    }
  }, [dismissed, fetchStatus]);

  if (dismissed && !needsRefresh) {
    return null;
  }

  return (
    <div className="pointer-events-none fixed bottom-5 right-4 z-40 flex max-w-[min(320px,calc(100%-32px))] flex-col items-end gap-3 sm:bottom-6 sm:right-6 md:bottom-8 md:right-8">
      <SystemStatusActions
        className="pointer-events-auto w-full"
        isReady={isReady}
        statusLoading={statusLoading}
        onRefresh={handleRefresh}
        onClose={() => setDismissed(true)}
      />
    </div>
  );
}
