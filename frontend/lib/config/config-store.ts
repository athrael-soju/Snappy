/**
 * Configuration storage utility for persisting runtime config in localStorage
 */

import {
  readStorageValue,
  removeStorageValue,
  writeJSONStorageValue,
} from "@/stores/utils/storage";

const CONFIG_STORAGE_KEY = "colpali-runtime-config";
const CONFIG_STORAGE_VERSION = 2;

export interface ConfigValues {
  [key: string]: string;
}

interface StoredConfigPayload {
  version: number;
  updatedAt: string;
  values: ConfigValues;
}

const DEFAULT_META = { updatedAt: null as Date | null };

function parseStoredPayload(raw: string | null): StoredConfigPayload | null {
  if (!raw) return null;

  try {
    const payload = JSON.parse(raw) as StoredConfigPayload | ConfigValues;
    if (
      payload &&
      typeof payload === "object" &&
      "version" in payload &&
      "values" in payload &&
      typeof (payload as StoredConfigPayload).version === "number"
    ) {
      const typed = payload as StoredConfigPayload;
      if (typed.version === CONFIG_STORAGE_VERSION && typed.values && typeof typed.values === "object") {
        return typed;
      }
    }

    // Backward compatibility: older versions stored raw values
    if (payload && typeof payload === "object" && !("version" in payload)) {
      return {
        version: CONFIG_STORAGE_VERSION,
        updatedAt: new Date().toISOString(),
        values: payload as ConfigValues,
      };
    }
  } catch (error) {
    console.error("Failed to parse config from localStorage:", error);
  }

  return null;
}

/**
 * Load configuration from localStorage
 */
export function loadConfigFromStorage(): ConfigValues | null {
  const payload = parseStoredPayload(readStorageValue(CONFIG_STORAGE_KEY));
  if (payload) {
    return payload.values;
  }

  return null;
}

/**
 * Save configuration to localStorage
 */
export function saveConfigToStorage(config: ConfigValues, updatedAt?: Date): boolean {
  try {
    const timestamp = updatedAt && !Number.isNaN(updatedAt.valueOf()) ? updatedAt : new Date();
    const payload: StoredConfigPayload = {
      version: CONFIG_STORAGE_VERSION,
      updatedAt: timestamp.toISOString(),
      values: config,
    };
    const success = writeJSONStorageValue(CONFIG_STORAGE_KEY, payload);
    if (!success) {
      console.error("Failed to save config to localStorage");
    }
    return success;
  } catch (error) {
    console.error("Failed to save config to localStorage:", error);
    return false;
  }
}

/**
 * Return stored metadata (updatedAt) if available
 */
export function loadStoredConfigMeta(): typeof DEFAULT_META {
  const payload = parseStoredPayload(readStorageValue(CONFIG_STORAGE_KEY));
  if (payload?.updatedAt) {
    const timestamp = new Date(payload.updatedAt);
    return { updatedAt: Number.isNaN(timestamp.valueOf()) ? null : timestamp };
  }

  return DEFAULT_META;
}

/**
 * Clear configuration from localStorage
 */
export function clearConfigFromStorage(): boolean {
  if (!removeStorageValue(CONFIG_STORAGE_KEY)) {
    console.error("Failed to clear config from localStorage");
    return false;
  }
  return true;
}

/**
 * Merge stored config with current values, preferring stored values
 */
export function mergeWithStoredConfig(currentValues: ConfigValues): ConfigValues {
  const stored = loadConfigFromStorage();
  if (!stored) return currentValues;

  // Merge with stored values taking precedence
  return {
    ...currentValues,
    ...stored,
  };
}
