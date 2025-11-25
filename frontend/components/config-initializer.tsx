"use client";

import { useEffect, useRef } from "react";
import { ConfigurationService } from "@/lib/api/generated";
import { loadConfigFromStorage } from "@/lib/config/config-store";
import { logger } from "@/lib/utils/logger";

/**
 * Syncs localStorage config to backend on app initialization.
 * Ensures backend has user's saved configuration preferences on startup.
 */
export function ConfigInitializer() {
  const hasInitialized = useRef(false);

  useEffect(() => {
    // Only run once
    if (hasInitialized.current) return;
    hasInitialized.current = true;

    const syncConfigToBackend = async () => {
      try {
        const storedValues = loadConfigFromStorage();
        if (!storedValues || Object.keys(storedValues).length === 0) {
          return; // No stored config to sync
        }

        // Get current backend values
        const serverValues = await ConfigurationService.getConfigValuesConfigValuesGet();

        // Find values that differ from backend
        const updates = Object.entries(storedValues).filter(
          ([key, value]) => serverValues[key as keyof typeof serverValues] !== value
        );

        if (updates.length === 0) {
          return; // Backend already has correct values
        }

        // Sync differences to backend
        await Promise.all(
          updates.map(([key, value]) =>
            ConfigurationService.updateConfigConfigUpdatePost({ key, value })
          )
        );

        logger.debug(`Synced ${updates.length} config value(s) from localStorage to backend`);
      } catch (error) {
        // Non-critical: config page will sync on next visit
        logger.warn("Failed to sync config on initialization", { error });
      }
    };

    syncConfigToBackend();
  }, []);

  return null; // This component renders nothing
}
