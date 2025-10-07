"use client";

import { useState, useEffect, forwardRef, useImperativeHandle } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { GlassPanel } from "@/components/ui/glass-panel";
import { Separator } from "@/components/ui/separator";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Skeleton } from "@/components/ui/skeleton";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { Settings, RotateCcw, AlertTriangle, Loader2 } from "lucide-react";
import { motion } from "framer-motion";
import { toast } from "sonner";
import { ConfigurationService, ApiError } from "@/lib/api/generated";
import "@/lib/api/client";
import { saveConfigToStorage, mergeWithStoredConfig, clearConfigFromStorage } from "@/lib/config/config-store";
import { ConfigurationTabs } from "@/components/configuration/configuration-tabs";
import { UnsavedChangesBar } from "@/components/configuration/unsaved-changes-bar";
import { SettingRenderer, type ConfigSetting } from "@/components/configuration/setting-renderer";

interface ConfigCategory {
  name: string;
  description: string;
  order: number;
  icon: string;
  settings: ConfigSetting[];
}

interface ConfigSchema {
  [categoryKey: string]: ConfigCategory;
}


export type ConfigurationPanelHandle = {
  openResetDialog: () => void;
};

export const ConfigurationPanel = forwardRef<ConfigurationPanelHandle, {}>((_, ref) => {
  const [values, setValues] = useState<Record<string, string>>({});
  const [originalValues, setOriginalValues] = useState<Record<string, string>>({});
  const [schema, setSchema] = useState<ConfigSchema | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState("application");
  const [resetDialogOpen, setResetDialogOpen] = useState(false);
  const [resetSectionDialogOpen, setResetSectionDialogOpen] = useState<string | null>(null);
  const [lastSaved, setLastSaved] = useState<Date | null>(null);

  useImperativeHandle(ref, () => ({
    openResetDialog: () => setResetDialogOpen(true),
  }));

  useEffect(() => {
    loadConfiguration();
  }, []);

  useEffect(() => {
    // Check if there are any changes
    const changed = Object.keys(values).some(key => values[key] !== originalValues[key]);
    setHasChanges(changed);
  }, [values, originalValues]);

  // Calculate stats for overview cards
  const configStats = {
    totalSettings: Object.keys(values).length,
    modifiedSettings: Object.keys(values).filter(key => values[key] !== originalValues[key]).length,
    enabledFeatures: [
      values.MUVERA_ENABLED === "True" ? "MUVERA" : null,
      values.QDRANT_MEAN_POOLING_ENABLED === "True" ? "Mean Pooling" : null,
      values.ENABLE_PIPELINE_INDEXING === "True" ? "Pipeline Indexing" : null,
      values.QDRANT_USE_BINARY === "True" ? "Binary Quantization" : null,
    ].filter(Boolean),
    currentMode: values.COLPALI_MODE || "gpu",
  };

  // Return early if schema not loaded
  if (!schema) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  async function loadConfiguration() {
    setLoading(true);
    setError(null);
    try {
      // Load schema and values from backend
      const [schemaData, valuesData] = await Promise.all([
        ConfigurationService.getConfigSchemaConfigSchemaGet(),
        ConfigurationService.getConfigValuesConfigValuesGet()
      ]);

      setSchema(schemaData as ConfigSchema);

      // Merge with localStorage (localStorage takes precedence)
      const mergedValues = mergeWithStoredConfig(valuesData);

      setValues(mergedValues);
      setOriginalValues(mergedValues);
    } catch (err) {
      const errorMsg = err instanceof ApiError ? err.message : "Failed to load configuration";
      setError(errorMsg);
      toast.error("Configuration Error", { description: errorMsg });
    } finally {
      setLoading(false);
    }
  }

  async function saveChanges() {
    setSaving(true);
    setError(null);

    try {
      const changedKeys = Object.keys(values).filter(key => values[key] !== originalValues[key]);

      // Update backend
      for (const key of changedKeys) {
        await ConfigurationService.updateConfigConfigUpdatePost({
          key,
          value: values[key]
        });
      }

      // Save to localStorage for persistence
      saveConfigToStorage(values);

      setOriginalValues({ ...values });
      setLastSaved(new Date());
      toast.success("Configuration saved", {
        description: `${changedKeys.length} setting${changedKeys.length !== 1 ? 's' : ''} updated`
      });
    } catch (err) {
      const errorMsg = err instanceof ApiError ? err.message : "Failed to save configuration";
      setError(errorMsg);
      toast.error("Save failed", { description: errorMsg });
    } finally {
      setSaving(false);
    }
  }

  function resetChanges() {
    setValues({ ...originalValues });
    setError(null);
    toast.info("Changes discarded");
  }

  async function resetSection(categoryKey: string) {
    if (!schema || !schema[categoryKey]) return;

    setSaving(true);
    setResetSectionDialogOpen(null);

    try {
      const category = schema[categoryKey];
      const defaultValues: Record<string, string> = {};

      for (const setting of category.settings) {
        defaultValues[setting.key] = setting.default;
        await ConfigurationService.updateConfigConfigUpdatePost({
          key: setting.key,
          value: setting.default
        });
      }

      setValues(prev => ({ ...prev, ...defaultValues }));
      setOriginalValues(prev => ({ ...prev, ...defaultValues }));
      saveConfigToStorage({ ...values, ...defaultValues });

      toast.success("Section reset", {
        description: `${category.name} settings restored to defaults`
      });
    } catch (err) {
      const errorMsg = err instanceof ApiError ? err.message : "Failed to reset section";
      toast.error("Reset failed", { description: errorMsg });
    } finally {
      setSaving(false);
    }
  }

  async function resetToDefaults() {
    setSaving(true);
    setError(null);
    setResetDialogOpen(false);

    try {
      // Clear localStorage
      clearConfigFromStorage();

      // Reset backend to defaults
      await ConfigurationService.resetConfigConfigResetPost();

      // Reload configuration
      await loadConfiguration();
      setLastSaved(new Date());

      toast.success("Configuration reset", { description: "All settings restored to defaults" });
    } catch (err) {
      const errorMsg = err instanceof ApiError ? err.message : "Failed to reset configuration";
      setError(errorMsg);
      toast.error("Reset failed", { description: errorMsg });
    } finally {
      setSaving(false);
    }
  }

  function handleValueChange(key: string, value: string) {
    setValues(prev => ({ ...prev, [key]: value }));
  }

  function isSettingVisible(setting: ConfigSetting): boolean {
    if (setting.ui_hidden) return false;
    // If no dependency, always visible
    if (!setting.depends_on) return true;

    // Check if parent setting has the required value
    const parentValue = values[setting.depends_on.key] || "";
    const parentBool = parentValue.toLowerCase() === "true";

    return parentBool === setting.depends_on.value;
  }


  if (loading) {
    return (
      <div className="container max-w-7xl py-8 space-y-4">
        <Skeleton className="h-8 w-48" />
        <div className="flex gap-6">
          <Skeleton className="h-96 w-48" />
          <div className="flex-1 space-y-4">
            <Skeleton className="h-12 w-full" />
            <Skeleton className="h-24 w-full" />
            <Skeleton className="h-24 w-full" />
          </div>
        </div>
      </div>
    );
  }

  const sortedCategories = Object.entries(schema).sort(([, a], [, b]) => a.order - b.order);
  const hiddenCategoryTerms = ["core application", "embedding model"];
  const filteredCategories = sortedCategories.filter(([_, category]) =>
    !hiddenCategoryTerms.some(term => category.name.toLowerCase().includes(term))
  );
  const baseCategories = filteredCategories.length > 0 ? filteredCategories : sortedCategories;
  const visibleCategories = baseCategories.filter(([_, category]) =>
    category.settings.some(setting => !setting.depends_on && isSettingVisible(setting))
  );
  const categoriesToRender = visibleCategories.length > 0 ? visibleCategories : baseCategories;
  const activeCategoryKey = categoriesToRender.some(([key]) => key === activeTab)
    ? activeTab
    : categoriesToRender[0]?.[0] ?? activeTab;

  return (
    <div className="flex flex-col h-full">
      {/* Error alert */}
      {error && (
        <div className="flex-shrink-0 mb-4">
          <Alert variant="destructive">
            <AlertTriangle className="h-4 w-4" />
            <AlertTitle>Error</AlertTitle>
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        </div>
      )}

      {/* Main content - with proper height constraints */}
      <div className="flex-1 min-h-0 flex gap-6 pr-4">
        {/* Left rail navigation */}
        <ConfigurationTabs
          categories={categoriesToRender}
          activeTab={activeCategoryKey}
          onTabChange={setActiveTab}
        />

        {/* Main content area */}
        <div className="flex-1 min-w-0 flex flex-col gap-4">
        <ScrollArea className="h-[calc(100vh-20rem)]">          
          {categoriesToRender.map(([categoryKey, category]) => {
            if (activeCategoryKey !== categoryKey) return null;

            // Filter to show only top-level settings (exclude nested children with depends_on)
            const visibleSettings = category.settings.filter(s => isSettingVisible(s) && !s.depends_on);

            return (
              <motion.div
                key={categoryKey}
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                transition={{ duration: 0.2 }}
                className="flex-1 min-h-0"
              >
                {/* Settings Card - Scrollable */}
                <GlassPanel className="flex flex-1 min-h-0 flex-col p-6 overflow-hidden">
                  <CardHeader className="pb-4 flex-shrink-0 px-0 pt-0">
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex items-start gap-3">
                        <div className="flex size-12 items-center justify-center rounded-xl bg-gradient-to-br from-blue-500/10 to-blue-500/5 text-blue-500">
                          <Settings className="w-6 h-6" />
                        </div>
                        <div>
                          <CardTitle className="text-xl font-semibold text-foreground">{category.name}</CardTitle>
                          <CardDescription className="mt-1 text-base leading-relaxed text-muted-foreground">{category.description}</CardDescription>
                        </div>
                      </div>
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => setResetSectionDialogOpen(categoryKey)}
                            disabled={saving}
                            className="h-9 w-9 shrink-0"
                          >
                            <RotateCcw className="w-4 h-4" />
                          </Button>
                        </TooltipTrigger>
                        <TooltipContent sideOffset={8} side="right" className="bg-popover text-popover-foreground">
                        <p>Reset this section</p>
                        </TooltipContent>
                      </Tooltip>
                    </div>
                  </CardHeader>

                    <CardContent className="flex-1 min-h-0 overflow-y-auto space-y-6 px-0 pb-0 rounded-3xl">
                      {visibleSettings.map((setting, index) => {
                        // Check for nested settings
                        const childSettings = category.settings.filter(
                          s => s.depends_on?.key === setting.key && isSettingVisible(s)
                        );
                        const hasChildren = childSettings.length > 0;

                        return (
                          <div key={setting.key}>
                            {index > 0 && <Separator className="my-3" />}
                            <SettingRenderer
                              setting={setting}
                              value={values[setting.key]}
                              saving={saving}
                              onChange={handleValueChange}
                            />

                            {/* Nested child settings */}
                            {hasChildren && (
                              <div className="mt-4 ml-8 pl-5 border-l-2 border-blue-300/40 dark:border-blue-800/40 space-y-4 pb-2">
                                {childSettings.map(childSetting => (
                                  <div key={childSetting.key}>
                                    <SettingRenderer
                                      setting={childSetting}
                                      value={values[childSetting.key]}
                                      saving={saving}
                                      isNested={true}
                                      onChange={handleValueChange}
                                    />
                                  </div>
                                ))}
                              </div>
                            )}
                          </div>
                        );
                      })}
                    </CardContent>

                </GlassPanel>

              </motion.div>
            );
          })}
          </ScrollArea>
        </div>
      </div>

      <UnsavedChangesBar
        hasChanges={hasChanges}
        saving={saving}
        modifiedCount={configStats.modifiedSettings}
        lastSaved={lastSaved}
        onSave={saveChanges}
        onDiscard={resetChanges}
      />
      {/* Reset All Dialog */}
      <Dialog open={resetDialogOpen} onOpenChange={setResetDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-destructive" />
              Reset all configuration?
            </DialogTitle>
            <DialogDescription>
              This will reset all configuration settings to their default values. Your saved configuration will be cleared from browser storage.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setResetDialogOpen(false)}
              disabled={saving}
            >
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={resetToDefaults}
              disabled={saving}
            >
              {saving ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Resetting...
                </>
              ) : (
                "Confirm Reset"
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>


      {/* Section Reset Dialog */}
      <Dialog open={!!resetSectionDialogOpen} onOpenChange={(open) => !open && setResetSectionDialogOpen(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <RotateCcw className="w-5 h-5 text-destructive" />
              Reset section?
            </DialogTitle>
            <DialogDescription>
              This will reset all {resetSectionDialogOpen && schema[resetSectionDialogOpen]?.name} settings to their defaults.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setResetSectionDialogOpen(null)}
              disabled={saving}
            >
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={() => resetSectionDialogOpen && resetSection(resetSectionDialogOpen)}
              disabled={saving}
            >
              {saving ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Resetting...
                </>
              ) : (
                "Reset Section"
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
});

ConfigurationPanel.displayName = "ConfigurationPanel";
