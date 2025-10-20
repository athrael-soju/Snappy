"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";

import { useSystemStatus } from "@/stores/app-store";
import {
  readStorageValue,
  removeStorageValue,
  writeStorageValue,
} from "@/stores/utils/storage";
import { SystemStatusActions, resolveSeverity } from "@/components/system-status-actions";

const FLOATING_VARIANTS = {
  hidden: { opacity: 0, y: 12, scale: 0.95 },
  visible: { opacity: 1, y: 0, scale: 1 },
};

const DISMISS_STORAGE_KEY = "morty-system-status-dismissed";

export function SystemStatusFloating() {
  const { statusLoading, fetchStatus, systemStatus } = useSystemStatus();
  const [dismissed, setDismissed] = useState(false);
  const severity = resolveSeverity(systemStatus);
  const previousSeverityRef = useRef<ReturnType<typeof resolveSeverity> | null>(null);

  const persistDismissal = useCallback(() => {
    writeStorageValue(DISMISS_STORAGE_KEY, "true");
  }, []);

  const clearDismissal = useCallback(() => {
    removeStorageValue(DISMISS_STORAGE_KEY);
  }, []);

  const handleRefresh = useCallback(() => {
    clearDismissal();
    setDismissed(false);
    void fetchStatus();
  }, [fetchStatus, clearDismissal]);

  const handleDismiss = useCallback(() => {
    setDismissed(true);
    if (severity === "ok") {
      persistDismissal();
    } else {
      clearDismissal();
    }
  }, [severity, clearDismissal, persistDismissal]);

  useEffect(() => {
    const handleMaintenance = () => {
      clearDismissal();
      setDismissed(false);
    };
    window.addEventListener("systemStatusChanged", handleMaintenance);
    return () => window.removeEventListener("systemStatusChanged", handleMaintenance);
  }, [clearDismissal]);

  useEffect(() => {
    const previous = previousSeverityRef.current;
    if (previous === "ok" && severity !== "ok") {
      setDismissed(false);
      clearDismissal();
    }
    previousSeverityRef.current = severity;
  }, [severity, clearDismissal]);

  useEffect(() => {
    if (severity === "ok") {
      const stored = readStorageValue(DISMISS_STORAGE_KEY);
      if (stored === "true") {
        setDismissed(true);
      }
    } else if (systemStatus) {
      clearDismissal();
      setDismissed(false);
    }
  }, [severity, systemStatus, clearDismissal]);

  const isVisible = !dismissed;

  return (
    <div className="pointer-events-none fixed bottom-5 right-4 z-40 flex max-w-[min(320px,calc(100%-32px))] flex-col items-end gap-3 sm:bottom-6 sm:right-6 md:bottom-8 md:right-8">
      <AnimatePresence>
        {isVisible ? (
          <motion.div
            key="system-status-floating"
            className="w-full"
            initial="hidden"
            animate="visible"
            exit="hidden"
            variants={FLOATING_VARIANTS}
            transition={{ duration: 0.3, ease: "easeOut" }}
          >
            <SystemStatusActions
              className="pointer-events-auto w-full"
              statusLoading={statusLoading}
              onRefresh={handleRefresh}
              onClose={handleDismiss}
              systemStatus={systemStatus}
            />
          </motion.div>
        ) : null}
      </AnimatePresence>
    </div>
  );
}
