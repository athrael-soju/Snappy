"use client";

import { useEffect, useRef } from "react";
import "@/lib/api/client";
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
        logger.debug("ConfigInitializer: Starting config sync from localStorage to backend");

        const storedValues = loadConfigFromStorage();
        if (!storedValues || Object.keys(storedValues).length === 0) {
          logger.debug("ConfigInitializer: No stored config found in localStorage");
          return;
        }

        logger.debug(`ConfigInitializer: Found ${Object.keys(storedValues).length} stored config values`, {
          keys: Object.keys(storedValues)
        });

        // Get current backend values
        const serverValues = await ConfigurationService.getConfigValuesConfigValuesGet();

        // Find values that differ from backend
        const updates = Object.entries(storedValues).filter(
          ([key, value]) => serverValues[key as keyof typeof serverValues] !== value
        );

        if (updates.length === 0) {
          logger.debug("ConfigInitializer: Backend already has correct values, no sync needed");
          return;
        }

        logger.info(`ConfigInitializer: Syncing ${updates.length} config value(s) to backend`, {
          updates: updates.map(([key, value]) => ({ key, value }))
        });

        // Sync differences to backend sequentially to avoid race conditions
        for (const [key, value] of updates) {
          try {
            await ConfigurationService.updateConfigConfigUpdatePost({ key, value });
            logger.debug(`ConfigInitializer: Synced ${key}=${value}`);
          } catch (error) {
            logger.error(`ConfigInitializer: Failed to sync ${key}`, { error });
          }
        }

        logger.info(`ConfigInitializer: Successfully synced ${updates.length} config value(s)`);
      } catch (error) {
        logger.error("ConfigInitializer: Failed to sync config on initialization", {
          error,
          errorMessage: error instanceof Error ? error.message : String(error)
        });
      }
    };

    // Add small delay to ensure server is ready
    const timeoutId = setTimeout(() => {
      syncConfigToBackend();
    }, 100);

    return () => clearTimeout(timeoutId);
  }, []);

  return null; // This component renders nothing
}
