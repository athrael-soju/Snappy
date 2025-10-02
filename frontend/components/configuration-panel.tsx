"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Slider } from "@/components/ui/slider";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { Settings, Save, RotateCcw, AlertTriangle, Loader2, Database, Cpu, Brain, HardDrive, HelpCircle } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { toast } from "@/components/ui/sonner";
import { ConfigurationService, ApiError } from "@/lib/api/generated";
import "@/lib/api/client";
import { saveConfigToStorage, mergeWithStoredConfig, clearConfigFromStorage } from "@/lib/config/config-store";

// Types for configuration schema
interface ConfigSetting {
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
}

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

// Icon mapping
const iconMap: Record<string, any> = {
  settings: Settings,
  cpu: Cpu,
  brain: Brain,
  database: Database,
  "hard-drive": HardDrive,
};

export function ConfigurationPanel() {
  const [values, setValues] = useState<Record<string, string>>({});
  const [originalValues, setOriginalValues] = useState<Record<string, string>>({});
  const [schema, setSchema] = useState<ConfigSchema | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState("application");
  const [resetDialogOpen, setResetDialogOpen] = useState(false);
  
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
      toast.success("Configuration Saved", { 
        description: `${changedKeys.length} setting(s) updated and saved to browser storage.` 
      });
    } catch (err) {
      const errorMsg = err instanceof ApiError ? err.message : "Failed to save configuration";
      setError(errorMsg);
      toast.error("Save Failed", { description: errorMsg });
    } finally {
      setSaving(false);
    }
  }

  function resetChanges() {
    setValues({ ...originalValues });
    setError(null);
    toast.info("Changes Discarded", { description: "All changes have been reverted" });
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
      
      toast.success("Reset Complete", { description: "All settings reset to defaults" });
    } catch (err) {
      const errorMsg = err instanceof ApiError ? err.message : "Failed to reset configuration";
      setError(errorMsg);
      toast.error("Reset Failed", { description: errorMsg });
    } finally {
      setSaving(false);
    }
  }

  function handleValueChange(key: string, value: string) {
    setValues(prev => ({ ...prev, [key]: value }));
  }

  function isSettingVisible(setting: ConfigSetting): boolean {
    // If no dependency, always visible
    if (!setting.depends_on) return true;
    
    // Check if parent setting has the required value
    const parentValue = values[setting.depends_on.key] || "";
    const parentBool = parentValue.toLowerCase() === "true";
    
    return parentBool === setting.depends_on.value;
  }

  function renderSetting(setting: ConfigSetting, isNested: boolean = false) {
    const currentValue = values[setting.key] || setting.default;

    switch (setting.type) {
      case "boolean":
        return (
          <div className="flex items-center justify-between space-x-2">
            <Label htmlFor={setting.key} className="flex-1">
              <div className="flex items-center gap-1.5">
                <span className="font-medium">{setting.label}</span>
                {setting.help_text && (
                  <TooltipProvider>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <HelpCircle className="w-3.5 h-3.5 text-muted-foreground cursor-help" />
                      </TooltipTrigger>
                      <TooltipContent className="max-w-xs">
                        <p className="text-sm">{setting.help_text}</p>
                      </TooltipContent>
                    </Tooltip>
                  </TooltipProvider>
                )}
              </div>
              <div className="text-xs text-muted-foreground mt-0.5">{setting.description}</div>
            </Label>
            <Switch
              id={setting.key}
              checked={currentValue.toLowerCase() === "true"}
              onCheckedChange={(checked) => handleValueChange(setting.key, checked ? "True" : "False")}
              disabled={saving}
            />
          </div>
        );

      case "select":
        return (
          <div className="space-y-2">
            <Label htmlFor={setting.key}>
              <div className="flex items-center gap-1.5">
                <span className="font-medium">{setting.label}</span>
                {setting.help_text && (
                  <TooltipProvider>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <HelpCircle className="w-3.5 h-3.5 text-muted-foreground cursor-help" />
                      </TooltipTrigger>
                      <TooltipContent className="max-w-xs">
                        <p className="text-sm">{setting.help_text}</p>
                      </TooltipContent>
                    </Tooltip>
                  </TooltipProvider>
                )}
              </div>
              <div className="text-xs text-muted-foreground mt-0.5">{setting.description}</div>
            </Label>
            <Select
              value={currentValue}
              onValueChange={(value) => handleValueChange(setting.key, value)}
              disabled={saving}
            >
              <SelectTrigger id={setting.key}>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {setting.options?.map(option => (
                  <SelectItem key={option} value={option}>
                    {option}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        );

      case "number":
        const numValue = parseFloat(currentValue) || parseFloat(setting.default);
        const min = setting.min ?? 0;
        const max = setting.max ?? 100;
        const step = setting.step ?? 1;

        if (isNested) {
          // Compact inline version for nested settings
          return (
            <div className="flex items-center gap-3">
              <Label htmlFor={setting.key} className="min-w-[120px] text-sm flex items-center gap-1.5">
                <span>{setting.label}</span>
                {setting.help_text && (
                  <TooltipProvider>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <HelpCircle className="w-3 h-3 text-muted-foreground cursor-help" />
                      </TooltipTrigger>
                      <TooltipContent className="max-w-xs">
                        <p className="text-sm">{setting.help_text}</p>
                      </TooltipContent>
                    </Tooltip>
                  </TooltipProvider>
                )}
              </Label>
              <Slider
                id={setting.key}
                value={[numValue]}
                min={min}
                max={max}
                step={step}
                onValueChange={(vals) => handleValueChange(setting.key, vals[0].toString())}
                disabled={saving}
                className="flex-1 max-w-[200px]"
              />
              <Input
                type="number"
                value={currentValue}
                onChange={(e) => handleValueChange(setting.key, e.target.value)}
                min={min}
                max={max}
                step={step}
                disabled={saving}
                className="w-20 h-8"
              />
            </div>
          );
        }

        return (
          <div className="space-y-3">
            <Label htmlFor={setting.key}>
              <div className="flex items-center gap-1.5">
                <span className="font-medium">{setting.label}</span>
                {setting.help_text && (
                  <TooltipProvider>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <HelpCircle className="w-3.5 h-3.5 text-muted-foreground cursor-help" />
                      </TooltipTrigger>
                      <TooltipContent className="max-w-xs">
                        <p className="text-sm">{setting.help_text}</p>
                      </TooltipContent>
                    </Tooltip>
                  </TooltipProvider>
                )}
              </div>
              <div className="text-xs text-muted-foreground mt-0.5">{setting.description}</div>
            </Label>
            <div className="flex items-center gap-4">
              <Slider
                id={setting.key}
                value={[numValue]}
                min={min}
                max={max}
                step={step}
                onValueChange={(vals) => handleValueChange(setting.key, vals[0].toString())}
                disabled={saving}
                className="flex-1"
              />
              <Input
                type="number"
                value={currentValue}
                onChange={(e) => handleValueChange(setting.key, e.target.value)}
                min={min}
                max={max}
                step={step}
                disabled={saving}
                className="w-24"
              />
            </div>
          </div>
        );

      case "password":
        return (
          <div className="space-y-2">
            <Label htmlFor={setting.key}>
              <div className="flex items-center gap-1.5">
                <span className="font-medium">{setting.label}</span>
                {setting.help_text && (
                  <TooltipProvider>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <HelpCircle className="w-3.5 h-3.5 text-muted-foreground cursor-help" />
                      </TooltipTrigger>
                      <TooltipContent className="max-w-xs">
                        <p className="text-sm">{setting.help_text}</p>
                      </TooltipContent>
                    </Tooltip>
                  </TooltipProvider>
                )}
              </div>
              <div className="text-xs text-muted-foreground mt-0.5">{setting.description}</div>
            </Label>
            <Input
              id={setting.key}
              type="password"
              value={currentValue}
              onChange={(e) => handleValueChange(setting.key, e.target.value)}
              disabled={saving}
              autoComplete="off"
            />
          </div>
        );

      default: // text
        return (
          <div className="space-y-2">
            <Label htmlFor={setting.key}>
              <div className="flex items-center gap-1.5">
                <span className="font-medium">{setting.label}</span>
                {setting.help_text && (
                  <TooltipProvider>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <HelpCircle className="w-3.5 h-3.5 text-muted-foreground cursor-help" />
                      </TooltipTrigger>
                      <TooltipContent className="max-w-xs">
                        <p className="text-sm">{setting.help_text}</p>
                      </TooltipContent>
                    </Tooltip>
                  </TooltipProvider>
                )}
              </div>
              <div className="text-xs text-muted-foreground mt-0.5">{setting.description}</div>
            </Label>
            <Input
              id={setting.key}
              type="text"
              value={currentValue}
              onChange={(e) => handleValueChange(setting.key, e.target.value)}
              disabled={saving}
            />
          </div>
        );
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
      </div>
    );
  }


  return (
    <div className="flex flex-col h-full">
      {/* Header */}


      {/* Action Buttons */}
      {hasChanges && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-center gap-3 p-4 rounded-lg border border-amber-200 bg-amber-50/50"
        >
          <AlertTriangle className="h-5 w-5 text-amber-600 flex-shrink-0" />
          <div className="flex-1">
            <p className="text-sm font-medium text-amber-900">
              You have {configStats.modifiedSettings} unsaved change{configStats.modifiedSettings !== 1 ? 's' : ''}
            </p>
            <p className="text-xs text-amber-700">
              Changes will take effect immediately but won't persist after restart
            </p>
          </div>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={resetChanges}
              disabled={saving}
            >
              <RotateCcw className="w-4 h-4 mr-2" />
              Discard
            </Button>
            <Button
              size="sm"
              onClick={saveChanges}
              disabled={saving}
              className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white"
            >
              {saving ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Saving...
                </>
              ) : (
                <>
                  <Save className="w-4 h-4 mr-2" />
                  Save {configStats.modifiedSettings} Change{configStats.modifiedSettings !== 1 ? 's' : ''}
                </>
              )}
            </Button>
          </div>
        </motion.div>
      )}

      {/* Status Messages */}
      <AnimatePresence>      
        {error && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
          >
            <Alert variant="destructive">
              <AlertTriangle className="h-4 w-4" />
              <AlertTitle>Error</AlertTitle>
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Configuration Categories - Using Tabs */}
      <Card className="flex-1 flex flex-col min-h-0">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full h-full flex flex-col">
          <CardHeader className="border-b flex-shrink-0 py-3">
            <TabsList className="grid w-full grid-cols-5 h-auto bg-transparent p-0 gap-1">
              {Object.entries(schema)
                .sort(([, a], [, b]) => a.order - b.order)
                .map(([categoryKey, category]) => {
                  const Icon = iconMap[category.icon] || Settings;
                  return (
                    <TabsTrigger
                      key={categoryKey}
                      value={categoryKey}
                      className="flex flex-col items-center gap-1.5 py-3 px-2 data-[state=active]:bg-primary/5 data-[state=active]:border-primary data-[state=active]:border-b-2 rounded-none"
                    >
                      <Icon className="w-5 h-5" />
                      <span className="text-xs font-medium hidden sm:inline">{category.name}</span>
                    </TabsTrigger>
                  );
                })}
            </TabsList>
          </CardHeader>

          <CardContent className="flex-1 overflow-y-auto pt-4 pb-2">
            {Object.entries(schema).map(([categoryKey, category]) => {
              const Icon = iconMap[category.icon] || Settings;
              
              // Group settings by parent/child relationship
              const parentSettings = category.settings.filter(s => !s.depends_on);
              
              return (
                <TabsContent key={categoryKey} value={categoryKey} className="mt-0 space-y-4 h-full">
                  {/* Category Header */}
                  <div className="flex items-start gap-3">
                    <div className="p-2 bg-gradient-to-br from-blue-500/10 to-purple-500/10 rounded-lg border">
                      <Icon className="w-5 h-5 text-primary" />
                    </div>
                    <div className="flex-1">
                      <h3 className="text-lg font-semibold tracking-tight">{category.name}</h3>
                      <p className="text-xs text-muted-foreground mt-0.5">{category.description}</p>
                    </div>
                  </div>

                  {/* Settings Grid - 2 Columns */}
                  <div className="grid gap-3 md:grid-cols-2">
                    {parentSettings.map(setting => {
                      // Find child settings for this parent
                      const childSettings = category.settings.filter(
                        s => s.depends_on?.key === setting.key && isSettingVisible(s)
                      );
                      const hasChildren = childSettings.length > 0;
                      
                      return (
                        <motion.div
                          key={setting.key}
                          initial={{ opacity: 0, y: 10 }}
                          animate={{ opacity: 1, y: 0 }}
                          exit={{ opacity: 0, y: -10 }}
                          transition={{ duration: 0.2 }}
                          className={hasChildren ? "md:col-span-2" : ""}
                        >
                          <Card className="h-full hover:shadow-md transition-shadow">
                            <CardContent className="pt-4 pb-4 space-y-3">
                              {renderSetting(setting, false)}
                              
                              {/* Nested child settings in a compact row */}
                              {hasChildren && (
                                <div className="mt-3 pt-3 border-t border-primary/20 bg-muted/30 -mx-6 px-6 py-3 rounded-b-lg">
                                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                                    {childSettings.map(childSetting => (
                                      <motion.div
                                        key={childSetting.key}
                                        initial={{ opacity: 0 }}
                                        animate={{ opacity: 1 }}
                                        transition={{ duration: 0.2 }}
                                      >
                                        {renderSetting(childSetting, true)}
                                      </motion.div>
                                    ))}
                                  </div>
                                </div>
                              )}
                            </CardContent>
                          </Card>
                        </motion.div>
                      );
                    })}
                  </div>
                </TabsContent>
              );
            })}
          </CardContent>
        </Tabs>
      </Card>

      {/* Reset to Defaults - Fixed Footer */}
      <Card className="border-red-200/50 mt-4 flex-shrink-0">
        <CardContent className="py-3 px-4">
          <div className="flex items-center justify-between">
            <div className="flex-1">
              <div className="font-semibold text-red-600 text-sm">Danger Zone</div>
              <p className="text-xs text-muted-foreground">
                Reset all configuration values to their defaults. This will affect the running application.
              </p>
            </div>
            <Dialog open={resetDialogOpen} onOpenChange={setResetDialogOpen}>
              <DialogTrigger asChild>
                <Button
                  variant="destructive"
                  disabled={saving}
                  size="sm"
                >
                  <RotateCcw className="w-4 h-4 mr-2" />
                  Reset All to Defaults
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-md">
                <DialogHeader>
                  <DialogTitle className="flex items-center gap-2 text-lg">
                    <RotateCcw className="w-5 h-5 text-red-600" />
                    Reset All Configuration?
                  </DialogTitle>
                  <DialogDescription className="text-base leading-relaxed pt-2">
                    ⚠️ This will permanently reset all configuration settings to their default values. 
                    Your saved configuration will be cleared from browser storage and the backend will be reset.
                  </DialogDescription>
                </DialogHeader>
                <div className="bg-muted/50 p-4 rounded-lg border-l-4 border-amber-400">
                  <div className="flex items-start gap-2">
                    <AlertTriangle className="w-4 h-4 text-amber-600 mt-0.5 flex-shrink-0" />
                    <p className="text-sm text-muted-foreground">
                      <strong>Important:</strong> This action cannot be reversed. The application will use default settings after reset.
                    </p>
                  </div>
                </div>
                <DialogFooter className="gap-2">
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
                    className="bg-red-600 hover:bg-red-700"
                  >
                    {saving ? (
                      <>
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        Resetting...
                      </>
                    ) : (
                      <>
                        <RotateCcw className="w-4 h-4 mr-2" />
                        Confirm Reset
                      </>
                    )}
                  </Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
