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
import type { ConfigValues } from "@/lib/config/config-store";

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
  depends_on?: {
    key: string;
    value: boolean;
  };
  ui_hidden?: boolean;
  ui_disabled?: boolean;
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
  const [storedDraft, setStoredDraft] = useState<ConfigValues | null>(null);
  const [storedDraftKeys, setStoredDraftKeys] = useState<string[]>([]);
  const [storedDraftUpdatedAt, setStoredDraftUpdatedAt] = useState<Date | null>(null);

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
      setValues(serverValues);
      setOriginalValues(serverValues);

      const storedValues = loadConfigFromStorage();
      const { updatedAt: storedUpdatedAt } = loadStoredConfigMeta();

      if (storedValues) {
        const diffKeys = Object.entries(storedValues)
          .filter(([key, storedValue]) => typeof storedValue === "string" && serverValues[key] !== storedValue)
          .map(([key]) => key);

        if (diffKeys.length > 0) {
          setStoredDraft(storedValues);
          setStoredDraftKeys(diffKeys);
          setStoredDraftUpdatedAt(storedUpdatedAt ?? null);
          setLastSaved(storedUpdatedAt ?? null);
        } else {
          const timestamp = storedUpdatedAt ?? new Date();
          saveConfigToStorage(serverValues, timestamp);
          setStoredDraft(null);
          setStoredDraftKeys([]);
          setStoredDraftUpdatedAt(null);
          setLastSaved(timestamp);
          notifyRuntimeConfigUpdated();
        }
      } else {
        const timestamp = new Date();
        saveConfigToStorage(serverValues, timestamp);
        setStoredDraft(null);
        setStoredDraftKeys([]);
        setStoredDraftUpdatedAt(null);
        setLastSaved(timestamp);
        notifyRuntimeConfigUpdated();
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

  const hasStoredDraft = storedDraftKeys.length > 0;

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
    }),
    [values, originalValues]
  );

  const restoreStoredDraft = useCallback(() => {
    if (!storedDraft) return;
    setValues(prev => ({ ...prev, ...storedDraft }));
    setStoredDraftKeys([]);
    toast.info("Draft restored", {
      description: "Review the changes below, then save to reapply them.",
    });
  }, [storedDraft]);

  const discardStoredDraft = useCallback(() => {
    setStoredDraft(null);
    setStoredDraftKeys([]);
    setStoredDraftUpdatedAt(null);
    saveConfigToStorage(originalValues, new Date());
    toast.info("Draft discarded", {
      description: "Local draft changes were removed. Current settings mirror the server.",
    });
  }, [originalValues]);

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
      setStoredDraft(null);
      setStoredDraftKeys([]);
      setStoredDraftUpdatedAt(savedAt);
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
        setStoredDraft(null);
        setStoredDraftKeys([]);
        setStoredDraftUpdatedAt(savedAt);
        notifyRuntimeConfigUpdated();

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
    [schema, values, notifyRuntimeConfigUpdated]
  );

  const resetToDefaults = useCallback(async () => {
    setSaving(true);
    setError(null);

    try {
      clearConfigFromStorage();
      await ConfigurationService.resetConfigConfigResetPost();
      await loadConfiguration();
      setLastSaved(new Date());
      notifyRuntimeConfigUpdated();

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
  }, [loadConfiguration, notifyRuntimeConfigUpdated]);

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
    hasStoredDraft,
    storedDraftUpdatedAt,
    storedDraftKeys,
    saveChanges,
    resetChanges,
    resetSection,
    resetToDefaults,
    restoreStoredDraft,
    discardStoredDraft,
    handleValueChange,
    isSettingVisible,
  };
}
