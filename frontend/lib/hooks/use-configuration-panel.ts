"use client";

import { useState, useEffect, useCallback, useMemo } from "react";
import { toast } from "sonner";
import { ConfigurationService, ApiError } from "@/lib/api/generated";
import "@/lib/api/client";
import { saveConfigToStorage, clearConfigFromStorage, loadConfigFromStorage, loadStoredConfigMeta } from "@/lib/config/config-store";

const RUNTIME_CONFIG_EVENT = "runtimeConfigUpdated";

export interface ConfigSetting {
  key: string;
  label: string;
  type: "text" | "number" | "boolean" | "select" | "password" | "multiselect";
  options?: string[];
  default: string;
  description: string;
  help_text?: string;
  min?: number;
  max?: number;
  step?: number;
  depends_on?:
  | { key: string; value: boolean | string }
  | Array<{ key: string; value: boolean | string }>;
  ui_hidden?: boolean;
  ui_disabled?: boolean;
  ui_indent_level?: number;
}

export interface ConfigCategory {
  name: string;
  description: string;
  order: number;
  icon: string;
  settings: ConfigSetting[];
  ui_hidden?: boolean;
}

export type ConfigSchema = Record<string, ConfigCategory>;

interface ConfigStats {
  totalSettings: number;
  modifiedSettings: number;
  enabledFeatures: string[];
}

export function useConfigurationPanel() {
  const [values, setValues] = useState<Record<string, string>>({});
  const [originalValues, setOriginalValues] = useState<Record<string, string>>({});
  const [schema, setSchema] = useState<ConfigSchema | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState("application");
  const [lastSaved, setLastSaved] = useState<Date | null>(null);
  const notifyRuntimeConfigUpdated = useCallback(() => {
    if (typeof window !== "undefined") {
      window.dispatchEvent(new Event(RUNTIME_CONFIG_EVENT));
    }
  }, []);

  const loadConfiguration = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const [schemaData, valuesData] = await Promise.all([
        ConfigurationService.getConfigSchemaConfigSchemaGet(),
        ConfigurationService.getConfigValuesConfigValuesGet(),
      ]);

      setSchema(schemaData as ConfigSchema);

      const serverValues = { ...(valuesData as Record<string, string>) };
      const storedValues = loadConfigFromStorage();
      const { updatedAt: storedUpdatedAt } = loadStoredConfigMeta();

      // Local storage keeps the user's preferred runtime overrides; reapply them if they differ from defaults.
      const filteredStoredValues =
        storedValues && typeof storedValues === "object"
          ? (Object.fromEntries(
            Object.entries(storedValues).filter(
              ([key, storedValue]) =>
                typeof storedValue === "string" && Object.prototype.hasOwnProperty.call(serverValues, key)
            )
          ) as Record<string, string>)
          : null;

      const effectiveValues = filteredStoredValues ? { ...serverValues, ...filteredStoredValues } : serverValues;

      setValues(effectiveValues);
      setOriginalValues(effectiveValues);

      const timestamp = storedUpdatedAt ?? new Date();
      saveConfigToStorage(effectiveValues, timestamp);
      setLastSaved(timestamp);

      let appliedOverrides = 0;

      if (filteredStoredValues) {
        const diffEntries = Object.entries(filteredStoredValues).filter(
          ([key, storedValue]) => serverValues[key] !== storedValue
        );

        if (diffEntries.length > 0) {
          try {
            for (const [key, value] of diffEntries) {
              await ConfigurationService.updateConfigConfigUpdatePost({ key, value });
              appliedOverrides += 1;
            }
          } catch (applyError) {
            const errorMsg =
              applyError instanceof ApiError
                ? applyError.message
                : "Failed to reapply stored configuration overrides";
            setError(errorMsg);
            toast.error("Configuration restore failed", { description: errorMsg });
          }
        }
      }

      notifyRuntimeConfigUpdated();
      if (appliedOverrides > 0) {
        toast.success("Configuration restored", {
          description: `${appliedOverrides} setting${appliedOverrides === 1 ? "" : "s"} re-applied from local storage`,
        });
        if (typeof window !== "undefined") {
          window.dispatchEvent(new Event("systemStatusChanged"));
        }
      }
    } catch (err) {
      const errorMsg = err instanceof ApiError ? err.message : "Failed to load configuration";
      setError(errorMsg);
      toast.error("Configuration Error", { description: errorMsg });
    } finally {
      setLoading(false);
    }
  }, [notifyRuntimeConfigUpdated]);

  useEffect(() => {
    loadConfiguration();
  }, [loadConfiguration]);

  useEffect(() => {
    const changed = Object.keys(values).some(key => values[key] !== originalValues[key]);
    setHasChanges(changed);
  }, [values, originalValues]);

  const configStats: ConfigStats = useMemo(
    () => ({
      totalSettings: Object.keys(values).length,
      modifiedSettings: Object.keys(values).filter(key => values[key] !== originalValues[key]).length,
      enabledFeatures: [
        values.MUVERA_ENABLED === "True" ? "MUVERA" : null,
        values.QDRANT_MEAN_POOLING_ENABLED === "True" ? "Mean Pooling" : null,
        values.ENABLE_PIPELINE_INDEXING === "True" ? "Pipeline Indexing" : null,
        values.QDRANT_USE_BINARY === "True" ? "Binary Quantization" : null,
        values.DEEPSEEK_OCR_ENABLED === "True" ? "DeepSeek OCR" : null,
      ].filter(Boolean) as string[],
    }),
    [values, originalValues]
  );

  const handleValueChange = useCallback(
    (key: string, value: string) => {
      if (schema) {
        for (const category of Object.values(schema)) {
          const setting = category.settings.find((item) => item.key === key);
          if (setting) {
            if (
              setting.ui_disabled &&
              value.toLowerCase() === "true"
            ) {
              return;
            }
            break;
          }
        }
      }

      setValues(prev => ({ ...prev, [key]: value }));
    },
    [schema]
  );

  const isSettingVisible = useCallback(
    (setting: ConfigSetting): boolean => {
      if (setting.ui_hidden) return false;
      if (!setting.depends_on) return true;

      // Normalize to array for consistent handling
      const dependencies = Array.isArray(setting.depends_on)
        ? setting.depends_on
        : [setting.depends_on];

      // All dependencies must be satisfied (AND logic)
      return dependencies.every(dep => {
        const parentValue = values[dep.key] || "";

        // Handle boolean dependencies
        if (typeof dep.value === "boolean") {
          const parentBool = parentValue.toLowerCase() === "true";
          return parentBool === dep.value;
        }

        // Handle string dependencies (e.g., mode === "locate")
        return parentValue === dep.value;
      });
    },
    [values]
  ); const saveChanges = useCallback(async () => {
    setSaving(true);
    setError(null);

    try {
      const changedKeys = Object.keys(values).filter(key => values[key] !== originalValues[key]);

      const savedAt = new Date();
      for (const key of changedKeys) {
        await ConfigurationService.updateConfigConfigUpdatePost({
          key,
          value: values[key],
        });
      }

      saveConfigToStorage(values, savedAt);
      setOriginalValues({ ...values });
      setLastSaved(savedAt);
      notifyRuntimeConfigUpdated();
      toast.success("Configuration saved", {
        description: `${changedKeys.length} setting${changedKeys.length !== 1 ? "s" : ""} updated`,
      });
      if (typeof window !== "undefined") {
        window.dispatchEvent(new Event("systemStatusChanged"));
      }
    } catch (err) {
      const errorMsg = err instanceof ApiError ? err.message : "Failed to save configuration";
      setError(errorMsg);
      toast.error("Save failed", { description: errorMsg });
    } finally {
      setSaving(false);
    }
  }, [values, originalValues, notifyRuntimeConfigUpdated]);

  const resetChanges = useCallback(() => {
    setValues({ ...originalValues });
    setError(null);
    toast.info("Changes discarded");
  }, [originalValues]);

  const resetSection = useCallback(
    (categoryKey: string) => {
      if (!schema || !schema[categoryKey]) return;

      setError(null);

      try {
        const category = schema[categoryKey];
        const defaultValues: Record<string, string> = {};

        // Collect default values for this category
        for (const setting of category.settings) {
          defaultValues[setting.key] = setting.default;
        }

        // Update local values only (doesn't save to backend)
        setValues(prev => ({ ...prev, ...defaultValues }));

        toast.info("Section reset to defaults", {
          description: `${category.name} settings reset. Click 'Save Changes' to apply.`,
        });
      } catch (err) {
        const errorMsg = err instanceof ApiError ? err.message : "Failed to reset section";
        setError(errorMsg);
        toast.error("Reset failed", { description: errorMsg });
      }
    },
    [schema]
  );

  const resetToDefaults = useCallback(() => {
    if (!schema) return;

    setError(null);

    try {
      const defaultValues: Record<string, string> = {};

      // Collect all default values from schema
      for (const category of Object.values(schema)) {
        for (const setting of category.settings) {
          defaultValues[setting.key] = setting.default;
        }
      }

      // Update local values only (doesn't save to backend)
      setValues(defaultValues);

      toast.info("Reset to defaults", {
        description: "All settings reset to defaults. Click 'Save Changes' to apply."
      });
    } catch (err) {
      const errorMsg = err instanceof ApiError ? err.message : "Failed to reset configuration";
      setError(errorMsg);
      toast.error("Reset failed", { description: errorMsg });
    }
  }, [schema]);

  return {
    schema,
    loading,
    saving,
    hasChanges,
    error,
    activeTab,
    setActiveTab,
    values,
    configStats,
    lastSaved,
    saveChanges,
    resetChanges,
    resetSection,
    resetToDefaults,
    handleValueChange,
    isSettingVisible,
  };
}
