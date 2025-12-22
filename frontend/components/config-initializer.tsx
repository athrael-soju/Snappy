"use client";

import { useEffect, useRef } from "react";
import "@/lib/api/client";
import { ConfigurationService } from "@/lib/api/generated";
import { loadConfigFromStorage } from "@/lib/config/config-store";
import { logger } from "@/lib/utils/logger";

const MAX_RETRIES = 5;
const INITIAL_DELAY_MS = 500;
const BACKOFF_MULTIPLIER = 2;

/**
 * Syncs localStorage config to backend on app initialization.
 * Ensures backend has user's saved configuration preferences on startup.
 * Uses exponential backoff retry to handle server cold starts.
 */
export function ConfigInitializer() {
  const hasInitialized = useRef(false);

  useEffect(() => {
    // Only run once
    if (hasInitialized.current) return;
    hasInitialized.current = true;

    const syncConfigToBackend = async (attempt: number = 1): Promise<boolean> => {
      try {
        logger.debug(`ConfigInitializer: Starting config sync (attempt ${attempt}/${MAX_RETRIES})`);

        const storedValues = loadConfigFromStorage();
        if (!storedValues || Object.keys(storedValues).length === 0) {
          logger.debug("ConfigInitializer: No stored config found in localStorage");
          return true; // Nothing to sync, considered success
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
          return true;
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
            // Continue with other updates even if one fails
          }
        }

        logger.info(`ConfigInitializer: Successfully synced ${updates.length} config value(s)`);

        // Dispatch event to notify other components that config has been synced
        window.dispatchEvent(new CustomEvent("runtimeConfigSynced"));

        return true;
      } catch (error) {
        logger.warn(`ConfigInitializer: Sync attempt ${attempt} failed`, {
          error,
          errorMessage: error instanceof Error ? error.message : String(error)
        });
        return false;
      }
    };

    const syncWithRetry = async () => {
      let delay = INITIAL_DELAY_MS;

      for (let attempt = 1; attempt <= MAX_RETRIES; attempt++) {
        // Wait before attempting (allows server to start up)
        await new Promise(resolve => setTimeout(resolve, delay));

        const success = await syncConfigToBackend(attempt);
        if (success) {
          return;
        }

        // Exponential backoff for next attempt
        delay = delay * BACKOFF_MULTIPLIER;

        if (attempt < MAX_RETRIES) {
          logger.debug(`ConfigInitializer: Retrying in ${delay}ms...`);
        }
      }

      logger.error(`ConfigInitializer: Failed to sync config after ${MAX_RETRIES} attempts`);
    };

    syncWithRetry();
  }, []);

  return null; // This component renders nothing
}
