"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Slider } from "@/components/ui/slider";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { Skeleton } from "@/components/ui/skeleton";
import { Settings, Save, RotateCcw, AlertTriangle, Loader2, Database, Cpu, Brain, HardDrive, HelpCircle, Clock } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { toast } from "sonner";
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
  ui_hidden?: boolean;
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
  const [resetSectionDialogOpen, setResetSectionDialogOpen] = useState<string | null>(null);
  const [lastSaved, setLastSaved] = useState<Date | null>(null);
  
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

  function renderSetting(setting: ConfigSetting, isNested: boolean = false) {
    const currentValue = values[setting.key] || setting.default;

    // Nested settings have compact styling
    if (isNested) {
      switch (setting.type) {
        case "boolean":
          return (
            <div className="space-y-2">
              <div className="flex items-center justify-between gap-4">
                <Label htmlFor={setting.key} className="text-xs font-medium flex items-center gap-1.5">
                  {setting.label}
                  {setting.help_text && (
                    <TooltipProvider>
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <HelpCircle className="w-3.5 h-3.5 text-muted-foreground cursor-help" />
                        </TooltipTrigger>
                        <TooltipContent className="max-w-xs">
                          <p className="text-xs">{setting.help_text}</p>
                        </TooltipContent>
                      </Tooltip>
                    </TooltipProvider>
                  )}
                </Label>
                <Switch
                  id={setting.key}
                  checked={currentValue.toLowerCase() === "true"}
                  onCheckedChange={(checked) => handleValueChange(setting.key, checked ? "True" : "False")}
                  disabled={saving}
                  className="scale-90"
                />
              </div>
              <p className="text-xs text-muted-foreground leading-relaxed">{setting.description}</p>
            </div>
          );
        case "number":
          const numValue = parseFloat(currentValue) || parseFloat(setting.default);
          const min = setting.min ?? 0;
          const max = setting.max ?? 100;
          const step = setting.step ?? 1;
          
          return (
            <div className="space-y-2.5">
              <Label htmlFor={setting.key} className="text-xs font-medium flex items-center gap-1.5">
                {setting.label}
                {setting.help_text && (
                  <TooltipProvider>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <HelpCircle className="w-3.5 h-3.5 text-muted-foreground cursor-help" />
                      </TooltipTrigger>
                      <TooltipContent className="max-w-xs">
                        <p className="text-xs">{setting.help_text}</p>
                      </TooltipContent>
                    </Tooltip>
                  </TooltipProvider>
                )}
              </Label>
              <div className="flex items-center gap-3">
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
                  className="w-20 h-9 text-sm"
                />
              </div>
              <p className="text-xs text-muted-foreground leading-relaxed">{setting.description}</p>
            </div>
          );
        default:
          return null;
      }
    }

    // Two-column layout: label+description left, control right
    switch (setting.type) {
      case "boolean":
        return (
          <div className="py-4 space-y-2">
            <div className="flex items-center justify-between gap-8">
              <Label htmlFor={setting.key} className="text-sm font-medium flex items-center gap-1.5">
                {setting.label}
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
              </Label>
              <Switch
                id={setting.key}
                checked={currentValue.toLowerCase() === "true"}
                onCheckedChange={(checked) => handleValueChange(setting.key, checked ? "True" : "False")}
                disabled={saving}
              />
            </div>
            <p className="text-sm text-muted-foreground">{setting.description}</p>
          </div>
        );

      case "select":
        return (
          <div className="grid grid-cols-[1fr,280px] gap-8 items-start py-4">
            <div className="space-y-0.5">
              <Label htmlFor={setting.key} className="text-sm font-medium flex items-center gap-1.5">
                {setting.label}
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
              </Label>
              <p className="text-sm text-muted-foreground">{setting.description}</p>
            </div>
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

        return (
          <div className="grid grid-cols-[1fr,280px] gap-8 items-start py-4">
            <div className="space-y-0.5">
              <Label htmlFor={setting.key} className="text-sm font-medium flex items-center gap-1.5">
                {setting.label}
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
              </Label>
              <p className="text-sm text-muted-foreground">
                {setting.description}
                {(min !== undefined || max !== undefined) && (
                  <span className="ml-1 text-xs">
                    ({min}–{max})
                  </span>
                )}
              </p>
            </div>
            <div className="flex items-center gap-3">
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
                className="w-20"
              />
            </div>
          </div>
        );

      case "password":
        return (
          <div className="grid grid-cols-[1fr,280px] gap-8 items-start py-4">
            <div className="space-y-0.5">
              <Label htmlFor={setting.key} className="text-sm font-medium flex items-center gap-1.5">
                {setting.label}
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
              </Label>
              <p className="text-sm text-muted-foreground">{setting.description}</p>
            </div>
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
          <div className="grid grid-cols-[1fr,280px] gap-8 items-start py-4">
            <div className="space-y-0.5">
              <Label htmlFor={setting.key} className="text-sm font-medium flex items-center gap-1.5">
                {setting.label}
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
              </Label>
              <p className="text-sm text-muted-foreground">{setting.description}</p>
            </div>
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

      {/* Main content - scrollable */}
      <div className="flex-1 min-h-0 overflow-hidden">
        {/* Vertical tabs layout */}
        <div className="flex gap-6 h-full">
          {/* Left rail navigation */}
          <nav className="w-48 flex-shrink-0">
            <ScrollArea className="h-full">
                <div className="space-y-1 pr-2">
                  {sortedCategories.map(([categoryKey, category]) => {
                    const Icon = iconMap[category.icon] || Settings;
                    const isActive = activeTab === categoryKey;
                    
                    return (
                      <button
                        key={categoryKey}
                        onClick={() => setActiveTab(categoryKey)}
                        className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-300 ${
                          isActive
                            ? 'bg-gradient-to-r from-blue-100/80 via-purple-100/80 to-blue-100/80 text-blue-700 border-2 border-blue-200/50 shadow-md'
                            : 'text-muted-foreground hover:bg-gradient-to-r hover:from-blue-50/50 hover:to-purple-50/50 hover:text-foreground border-2 border-transparent'
                        }`}
                      >
                        <Icon className="w-4 h-4 flex-shrink-0" />
                        <span className="truncate text-left">{category.name}</span>
                      </button>
                    );
                  })}
                </div>
              </ScrollArea>
            </nav>

          {/* Main content area */}
          <div className="flex-1 min-w-0 flex flex-col gap-4">
            {sortedCategories.map(([categoryKey, category]) => {
              if (activeTab !== categoryKey) return null;
              
              const Icon = iconMap[category.icon] || Settings;
              // Filter to show only top-level settings (exclude nested children with depends_on)
              const visibleSettings = category.settings.filter(s => isSettingVisible(s) && !s.depends_on);
              
              return (
                <motion.div
                  key={categoryKey}
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                  transition={{ duration: 0.2 }}
                  className="flex-1 min-h-0 flex flex-col gap-4"
                >
                  {/* Settings Card - Scrollable */}
                  <Card className="flex-1 min-h-0 flex flex-col border-2 border-blue-200/50 bg-gradient-to-br from-blue-500/5 to-purple-500/5 shadow-lg hover:shadow-xl transition-shadow duration-300">
                    <CardHeader className="pb-4 flex-shrink-0">
                      <div className="flex items-start justify-between">
                        <div className="flex items-start gap-3">
                          <div className="p-2 bg-white rounded-xl border-2 border-blue-200/50 shadow-sm">
                            <Icon className="w-5 h-5 text-blue-500" />
                          </div>
                          <div>
                            <CardTitle className="text-xl font-bold">{category.name}</CardTitle>
                            <CardDescription className="mt-1 text-base">{category.description}</CardDescription>
                          </div>
                        </div>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => setResetSectionDialogOpen(categoryKey)}
                          disabled={saving}
                          className="text-muted-foreground hover:text-blue-600 hover:bg-blue-50"
                        >
                          <RotateCcw className="w-4 h-4 mr-2" />
                          Reset section
                        </Button>
                      </div>
                    </CardHeader>
                    <ScrollArea className="flex-1 min-h-0">
                      <CardContent className="pr-4 py-4">
                        {visibleSettings.map((setting, index) => {
                          // Check for nested settings
                          const childSettings = category.settings.filter(
                            s => s.depends_on?.key === setting.key && isSettingVisible(s)
                          );
                          const hasChildren = childSettings.length > 0;
                          
                          return (
                            <div key={setting.key}>
                              {index > 0 && <Separator className="my-3" />}
                              {renderSetting(setting)}
                              
                              {/* Nested child settings */}
                              {hasChildren && (
                                <div className="mt-4 ml-8 pl-5 border-l-2 border-blue-300/40 space-y-4 pb-2">
                                  {childSettings.map(childSetting => (
                                    <div key={childSetting.key}>
                                      {renderSetting(childSetting, true)}
                                    </div>
                                  ))}
                                </div>
                              )}
                            </div>
                          );
                        })}
                      </CardContent>
                    </ScrollArea>
                  </Card>

                  {/* Reset All - Compact button */}
                  <div className="flex justify-end flex-shrink-0">
                    <Dialog open={resetDialogOpen} onOpenChange={setResetDialogOpen}>
                      <DialogTrigger asChild>
                        <Button 
                          variant="outline" 
                          size="sm" 
                          disabled={saving} 
                          className="border-red-200 text-red-600 hover:bg-red-50 hover:text-red-700 hover:border-red-300 transition-all duration-300 rounded-full"
                        >
                          <RotateCcw className="w-3.5 h-3.5 mr-2" />
                          Reset All to Defaults
                        </Button>
                      </DialogTrigger>
                      <DialogContent>
                        <DialogHeader>
                          <DialogTitle className="flex items-center gap-2">
                            <AlertTriangle className="w-5 h-5 text-destructive" />
                            Reset all configuration?
                          </DialogTitle>
                          <DialogDescription>
                            This will reset all configuration settings to their default values. 
                            Your saved configuration will be cleared from browser storage.
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
                  </div>
                </motion.div>
              );
            })}
          </div>
        </div>
      </div>

      <AnimatePresence>
        {hasChanges && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 10 }}
            className="border-t-2 border-blue-200/50 bg-gradient-to-r from-blue-50/95 via-purple-50/95 to-cyan-50/95 backdrop-blur-sm shadow-2xl"
          >
            <div className="container max-w-7xl py-4 px-6">
              <div className="flex items-center gap-3">
                <div className="flex items-center gap-2 flex-1">
                  <div className="p-1.5 rounded-full bg-gradient-to-r from-blue-500 to-purple-500 shadow-md">
                    <AlertTriangle className="h-3.5 w-3.5 text-white" />
                  </div>
                  <p className="text-sm font-medium bg-gradient-to-r from-blue-600 via-purple-600 to-cyan-600 bg-clip-text text-transparent">
                    You have {configStats.modifiedSettings} unsaved change{configStats.modifiedSettings !== 1 ? 's' : ''}
                  </p>
                </div>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={resetChanges}
                    disabled={saving}
                    className="border-blue-200 hover:bg-blue-50 rounded-full"
                  >
                    Discard
                  </Button>
                  <Button
                    size="sm"
                    onClick={saveChanges}
                    disabled={saving}
                    className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white shadow-lg hover:shadow-xl transition-all duration-300 rounded-full"
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
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

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
}
