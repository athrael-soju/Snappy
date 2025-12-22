"use client";

import { useEffect, useState } from "react";
import { loadConfigFromStorage } from "@/lib/config/config-store";

const RUNTIME_CONFIG_EVENT = "runtimeConfigUpdated";
const RUNTIME_CONFIG_SYNCED_EVENT = "runtimeConfigSynced";

/**
 * Hook to check if mean pooling (reranking) is enabled in the configuration.
 * Listens for runtime config updates and returns the current state.
 */
export function useMeanPoolingEnabled(): boolean {
  const [enabled, setEnabled] = useState<boolean>(false);

  useEffect(() => {
    const checkConfig = () => {
      const config = loadConfigFromStorage();
      const isEnabled = config?.QDRANT_MEAN_POOLING_ENABLED === "True";
      setEnabled(isEnabled);
    };

    // Check on mount
    checkConfig();

    // Listen for runtime config updates and sync events
    const handleConfigUpdate = () => {
      checkConfig();
    };

    window.addEventListener(RUNTIME_CONFIG_EVENT, handleConfigUpdate);
    window.addEventListener(RUNTIME_CONFIG_SYNCED_EVENT, handleConfigUpdate);

    return () => {
      window.removeEventListener(RUNTIME_CONFIG_EVENT, handleConfigUpdate);
      window.removeEventListener(RUNTIME_CONFIG_SYNCED_EVENT, handleConfigUpdate);
    };
  }, []);

  return enabled;
}
