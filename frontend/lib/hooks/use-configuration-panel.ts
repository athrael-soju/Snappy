"use client";

import { useState, useEffect, useCallback, useMemo } from "react";
import { toast } from "sonner";
import { ConfigurationService, ApiError } from "@/lib/api/generated";
import "@/lib/api/client";
import {
  saveConfigToStorage,
  clearConfigFromStorage,
  loadConfigFromStorage,
  loadStoredConfigMeta,
} from "@/lib/config/config-store";
import { parseOptimizationResponse } from "@/lib/api/runtime";

export interface ConfigSetting {
  key: string;
  label: string;
  type: "text" | "number" | "boolean" | "select" | "password";
  options?: string[];
  default: string;
  description: string;
  help_text?: string;
  min?: number;
  max?: number;
  step?: number;
  depends_on?: {
    key: string;
    value: boolean;
  };
  ui_hidden?: boolean;
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
  currentMode: string;
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
  const [optimizing, setOptimizing] = useState(false);

  const loadConfiguration = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const [schemaData, valuesData] = await Promise.all([
        ConfigurationService.getConfigSchemaConfigSchemaGet(),
        ConfigurationService.getConfigValuesConfigValuesGet(),
      ]);

      setSchema(schemaData as ConfigSchema);

      const currentValues = { ...(valuesData as Record<string, string>) };
      const storedValues = loadConfigFromStorage();
      const { updatedAt: storedUpdatedAt } = loadStoredConfigMeta();
      const pendingUpdates: Array<[string, string]> = [];

      let appliedStoredConfig = false;
      if (storedValues) {
        for (const [key, storedValue] of Object.entries(storedValues)) {
          if (typeof storedValue !== "string") continue;
          if (currentValues[key] !== storedValue) {
            pendingUpdates.push([key, storedValue]);
          }
        }

        if (pendingUpdates.length > 0) {
          for (const [key, value] of pendingUpdates) {
            try {
              await ConfigurationService.updateConfigConfigUpdatePost({ key, value });
              currentValues[key] = value;
              appliedStoredConfig = true;
            } catch (err) {
              console.error(`Failed to reapply stored config for '${key}':`, err);
            }
          }
        }
      }

      setValues(currentValues);
      setOriginalValues(currentValues);
      const timestamp = appliedStoredConfig ? new Date() : storedUpdatedAt ?? new Date();
      saveConfigToStorage(currentValues, timestamp);
      setLastSaved(timestamp);

      if (appliedStoredConfig && typeof window !== "undefined") {
        window.dispatchEvent(new Event("systemStatusChanged"));
      }
    } catch (err) {
      const errorMsg = err instanceof ApiError ? err.message : "Failed to load configuration";
      setError(errorMsg);
      toast.error("Configuration Error", { description: errorMsg });
    } finally {
      setLoading(false);
    }
  }, []);

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
      ].filter(Boolean) as string[],
      currentMode: values.COLPALI_MODE || "gpu",
    }),
    [values, originalValues]
  );

  const handleValueChange = useCallback((key: string, value: string) => {
    setValues(prev => ({ ...prev, [key]: value }));
  }, []);

  const isSettingVisible = useCallback(
    (setting: ConfigSetting): boolean => {
      if (setting.ui_hidden) return false;
      if (!setting.depends_on) return true;

      const parentValue = values[setting.depends_on.key] || "";
      const parentBool = parentValue.toLowerCase() === "true";

      return parentBool === setting.depends_on.value;
    },
    [values]
  );

  const saveChanges = useCallback(async () => {
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
  }, [values, originalValues]);

  const resetChanges = useCallback(() => {
    setValues({ ...originalValues });
    setError(null);
    toast.info("Changes discarded");
  }, [originalValues]);

  const resetSection = useCallback(
    async (categoryKey: string) => {
      if (!schema || !schema[categoryKey]) return;

      setSaving(true);
      setError(null);

      try {
        const category = schema[categoryKey];
        const defaultValues: Record<string, string> = {};

        for (const setting of category.settings) {
          defaultValues[setting.key] = setting.default;
          await ConfigurationService.updateConfigConfigUpdatePost({
            key: setting.key,
            value: setting.default,
          });
        }

        const nextValues = { ...values, ...defaultValues };
        setValues(nextValues);
        setOriginalValues(prev => ({ ...prev, ...defaultValues }));
        const savedAt = new Date();
        saveConfigToStorage(nextValues, savedAt);

        toast.success("Section reset", {
          description: `${category.name} settings restored to defaults`,
        });
        setLastSaved(savedAt);
        if (typeof window !== "undefined") {
          window.dispatchEvent(new Event("systemStatusChanged"));
        }
      } catch (err) {
        const errorMsg = err instanceof ApiError ? err.message : "Failed to reset section";
        setError(errorMsg);
        toast.error("Reset failed", { description: errorMsg });
      } finally {
        setSaving(false);
      }
    },
    [schema, values]
  );

  const resetToDefaults = useCallback(async () => {
    setSaving(true);
    setError(null);

    try {
      clearConfigFromStorage();
      await ConfigurationService.resetConfigConfigResetPost();
      await loadConfiguration();
      setLastSaved(new Date());

      toast.success("Configuration reset", { description: "All settings restored to defaults" });
      if (typeof window !== "undefined") {
        window.dispatchEvent(new Event("systemStatusChanged"));
      }
    } catch (err) {
      const errorMsg = err instanceof ApiError ? err.message : "Failed to reset configuration";
      setError(errorMsg);
      toast.error("Reset failed", { description: errorMsg });
    } finally {
      setSaving(false);
    }
  }, [loadConfiguration]);

  const optimizeForSystem = useCallback(async () => {
    if (hasChanges) {
      toast.info("Save changes first", { description: "Please save or discard edits before optimizing." });
      return;
    }

    setOptimizing(true);
    setError(null);

    try {
      const result = await ConfigurationService.optimizeConfigConfigOptimizePost();
      const optimization = parseOptimizationResponse(result);
      clearConfigFromStorage();
      await loadConfiguration();
      setLastSaved(new Date());

      const appliedCount = Object.keys(optimization.applied ?? {}).length;
      const description =
        optimization.message ||
        (appliedCount
          ? `Applied ${appliedCount} setting${appliedCount !== 1 ? "s" : ""}.`
          : "Your configuration already matched the recommended profile.");

      const notify = appliedCount > 0 ? toast.success : toast.info;
      notify("Optimization complete", { description });
      if (typeof window !== "undefined") {
        window.dispatchEvent(new Event("systemStatusChanged"));
      }
    } catch (err) {
      const errorMsg = err instanceof ApiError ? err.message : "Failed to optimize configuration";
      setError(errorMsg);
      toast.error("Optimization failed", { description: errorMsg });
    } finally {
      setOptimizing(false);
    }
  }, [hasChanges, loadConfiguration]);

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
    optimizing,
    saveChanges,
    resetChanges,
    resetSection,
    resetToDefaults,
    optimizeForSystem,
    handleValueChange,
    isSettingVisible,
  };
}
