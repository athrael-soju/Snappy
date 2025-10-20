"use client";

import { useCallback, useEffect, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";

import { SystemStatusActions } from "@/components/system-status-actions";
import { useSystemStatus } from "@/stores/app-store";

const FLOATING_VARIANTS = {
  hidden: { opacity: 0, y: 12, scale: 0.95 },
  visible: { opacity: 1, y: 0, scale: 1 },
};

export function SystemStatusFloating() {
  const { isReady, statusLoading, fetchStatus, needsRefresh, systemStatus } = useSystemStatus();
  const [dismissed, setDismissed] = useState(false);

  const handleRefresh = useCallback(() => {
    void fetchStatus();
    if (dismissed) {
      setDismissed(false);
    }
  }, [dismissed, fetchStatus]);

  useEffect(() => {
    const handleMaintenance = () => setDismissed(false);
    window.addEventListener("systemStatusChanged", handleMaintenance);
    return () => window.removeEventListener("systemStatusChanged", handleMaintenance);
  }, []);

  const isVisible = !dismissed || needsRefresh;

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
              onClose={() => setDismissed(true)}
              systemStatus={systemStatus}
            />
          </motion.div>
        ) : null}
      </AnimatePresence>
    </div>
  );
}
