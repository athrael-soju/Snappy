"use client";

import { useState, useEffect, forwardRef, useImperativeHandle } from "react";
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
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
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

function formatRelativeTime(date: Date): string {
  const diffMs = Date.now() - date.getTime();
  const minute = 60 * 1000;
  const hour = 60 * minute;
  const day = 24 * hour;

  if (diffMs < minute) {
    return "Last saved moments ago.";
  }
  if (diffMs < hour) {
    const minutes = Math.max(1, Math.round(diffMs / minute));
    return `Last saved ${minutes} minute${minutes === 1 ? "" : "s"} ago.`;
  }
  if (diffMs < day) {
    const hours = Math.max(1, Math.round(diffMs / hour));
    return `Last saved ${hours} hour${hours === 1 ? "" : "s"} ago.`;
  }
  const days = Math.max(1, Math.round(diffMs / day));
  return `Last saved ${days} day${days === 1 ? "" : "s"} ago.`;
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

      {/* Main content - scrollable */}
      <ScrollArea className="flex-1 min-h-0">
        {/* Vertical tabs layout */}
        <div className="flex gap-6 h-full pr-4">
          {/* Left rail navigation */}
          <nav className="w-48 flex-shrink-0">
            <ScrollArea className="h-full">
                <div className="space-y-1 pr-2">
                  {categoriesToRender.map(([categoryKey, category]) => {
                    const Icon = iconMap[category.icon] || Settings;
                    const isActive = activeCategoryKey === categoryKey;
                    
                    return (
                      <button
                        key={categoryKey}
                        onClick={() => setActiveTab(categoryKey)}
                        className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-300 ${
                          isActive
                            ? 'bg-gradient-to-r from-blue-100 via-purple-100 to-blue-100 dark:from-blue-900/40 dark:via-purple-900/40 dark:to-blue-900/40 text-blue-700 dark:text-blue-200 border-2 border-blue-200 dark:border-blue-800/50 shadow-md'
                            : 'text-muted-foreground hover:bg-gradient-to-r hover:from-blue-50 hover:to-purple-50 dark:hover:from-blue-950/30 dark:hover:to-purple-950/30 hover:text-foreground border-2 border-transparent'
                        }`}
                      >
                        <Icon className={`w-4 h-4 flex-shrink-0 ${isActive ? 'text-blue-600 dark:text-blue-400' : ''}`} />
                        <span className="truncate text-left">{category.name}</span>
                      </button>
                    );
                  })}
                </div>
              </ScrollArea>
            </nav>

          {/* Main content area */}
          <div className="flex-1 min-w-0 flex flex-col gap-4">
            {categoriesToRender.map(([categoryKey, category]) => {
              if (activeCategoryKey !== categoryKey) return null;
              
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
                  <Card className="card-surface flex flex-col max-h-[600px] border-2">
                    <CardHeader className="pb-4 flex-shrink-0">
                      <div className="flex items-start justify-between">
                        <div className="flex items-start gap-3">
                          <div className="p-2 bg-white dark:bg-blue-900/40 rounded-xl border-2 border-blue-200 dark:border-blue-800/50 shadow-sm">
                            <Icon className="w-5 h-5 text-blue-500 dark:text-blue-400" />
                          </div>
                          <div>
                            <CardTitle className="text-xl font-bold text-foreground">{category.name}</CardTitle>
                            <CardDescription className="mt-1 text-base text-muted-foreground">{category.description}</CardDescription>
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

                </motion.div>
              );
            })}
          </div>
        </div>
      </ScrollArea>

      <AnimatePresence>
        {hasChanges && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 10 }}
          >
            <div className="container max-w-7xl py-4 px-4 sm:px-6">
              <div className="flex flex-col gap-4 rounded-2xl border border-blue-200/70 p-4 shadow-xl sm:flex-row sm:items-center sm:justify-between">
                <div className="flex items-start gap-3">
                  <div className="p-2 rounded-full bg-gradient-to-r from-blue-500 via-purple-500 to-cyan-500 text-white shadow-md">
                    <AlertTriangle className="h-4 w-4" />
                  </div>
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <p className="text-sm font-semibold text-slate-900 sm:text-base">
                        Unsaved configuration changes
                      </p>
                      <Badge variant="outline" className="border-blue-300 bg-blue-50 text-blue-700">
                        {configStats.modifiedSettings}
                      </Badge>
                    </div>
                    <p className="text-xs text-slate-600 sm:text-sm">
                      You have {configStats.modifiedSettings} pending change{configStats.modifiedSettings !== 1 ? 's' : ''}.{' '}
                      {lastSaved ? formatRelativeTime(lastSaved) : "No previous save recorded yet."}
                    </p>
                  </div>
                </div>
                <div className="flex flex-wrap items-center gap-2 sm:justify-end">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={resetChanges}
                    disabled={saving}
                    className="rounded-full border-blue-200 px-4 py-2 hover:bg-blue-50"
                  >
                    Discard
                  </Button>
                  <Button
                    size="sm"
                    onClick={saveChanges}
                    disabled={saving}
                    className="rounded-full bg-gradient-to-r from-blue-600 to-purple-600 px-4 py-2 text-white shadow-lg transition-all duration-300 hover:from-blue-700 hover:to-purple-700 hover:shadow-xl"
                  >
                    {saving ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Saving...
                      </>
                    ) : (
                      <>
                        <Save className="mr-2 h-4 w-4" />
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
