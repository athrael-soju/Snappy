/**
 * Configuration storage utility for persisting runtime config in localStorage
 */

const CONFIG_STORAGE_KEY = 'snappy-runtime-config';

export interface ConfigValues {
  [key: string]: string;
}

/**
 * Load configuration from localStorage
 */
export function loadConfigFromStorage(): ConfigValues | null {
  if (typeof window === 'undefined') return null;
  
  try {
    const stored = localStorage.getItem(CONFIG_STORAGE_KEY);
    if (stored) {
      return JSON.parse(stored);
    }
  } catch (error) {
    console.error('Failed to load config from localStorage:', error);
  }
  
  return null;
}

/**
 * Save configuration to localStorage
 */
export function saveConfigToStorage(config: ConfigValues): boolean {
  if (typeof window === 'undefined') return false;
  
  try {
    localStorage.setItem(CONFIG_STORAGE_KEY, JSON.stringify(config));
    return true;
  } catch (error) {
    console.error('Failed to save config to localStorage:', error);
    return false;
  }
}

/**
 * Clear configuration from localStorage
 */
export function clearConfigFromStorage(): boolean {
  if (typeof window === 'undefined') return false;
  
  try {
    localStorage.removeItem(CONFIG_STORAGE_KEY);
    return true;
  } catch (error) {
    console.error('Failed to clear config from localStorage:', error);
    return false;
  }
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
    ...stored
  };
}
