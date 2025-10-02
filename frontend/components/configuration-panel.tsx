"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Slider } from "@/components/ui/slider";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Settings, Save, RotateCcw, AlertTriangle, Loader2 } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { toast } from "@/components/ui/sonner";
import { ConfigurationService, ApiError } from "@/lib/api/generated";
import "@/lib/api/client";
import { CONFIG_SCHEMA, type ConfigSetting, type ConfigSchema } from "@/lib/config/schema";
import { saveConfigToStorage, mergeWithStoredConfig, clearConfigFromStorage } from "@/lib/config/config-store";

export function ConfigurationPanel() {
  const [values, setValues] = useState<Record<string, string>>({});
  const [originalValues, setOriginalValues] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadConfiguration();
  }, []);

  useEffect(() => {
    // Check if there are any changes
    const changed = Object.keys(values).some(key => values[key] !== originalValues[key]);
    setHasChanges(changed);
  }, [values, originalValues]);

  async function loadConfiguration() {
    setLoading(true);
    setError(null);
    try {
      // Load current values from backend
      const valuesData = await ConfigurationService.getConfigValuesConfigValuesGet();
      
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
    if (!confirm("Reset all settings to default values? This will clear your saved configuration.")) {
      return;
    }

    setSaving(true);
    setError(null);

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

  function renderSetting(setting: ConfigSetting) {
    const currentValue = values[setting.key] || setting.default;

    switch (setting.type) {
      case "boolean":
        return (
          <div className="flex items-center justify-between space-x-2">
            <Label htmlFor={setting.key} className="flex-1">
              <div className="font-medium">{setting.label}</div>
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
              <div className="font-medium">{setting.label}</div>
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

        return (
          <div className="space-y-3">
            <Label htmlFor={setting.key}>
              <div className="font-medium">{setting.label}</div>
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
              <div className="font-medium">{setting.label}</div>
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
              <div className="font-medium">{setting.label}</div>
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
    <div className="space-y-6">
      {/* Header with Actions */}
      <div className="flex items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold">Runtime Configuration</h2>
          <p className="text-sm text-muted-foreground">
            Adjust settings dynamically. Changes take effect immediately but won't persist after restart.
          </p>
        </div>
        <div className="flex gap-2">
          {hasChanges && (
            <Button
              variant="outline"
              size="sm"
              onClick={resetChanges}
              disabled={saving}
            >
              <RotateCcw className="w-4 h-4 mr-2" />
              Discard
            </Button>
          )}
          <Button
            size="sm"
            onClick={saveChanges}
            disabled={!hasChanges || saving}
            className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white shadow-lg"
          >
            {saving ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Saving...
              </>
            ) : (
              <>
                <Save className="w-4 h-4 mr-2" />
                Save Changes
              </>
            )}
          </Button>
        </div>
      </div>

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

      {/* Configuration Categories - Using Accordions */}
      <Accordion type="single" defaultValue="application" collapsible className="space-y-4">
        {Object.entries(CONFIG_SCHEMA).map(([categoryKey, category]) => (
          <AccordionItem key={categoryKey} value={categoryKey} className="border rounded-lg bg-card shadow-sm hover:shadow-md transition-shadow">
            <AccordionTrigger className="px-6 py-4 hover:no-underline hover:bg-gradient-to-r hover:from-blue-50/50 hover:to-purple-50/50 rounded-t-lg transition-colors">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-gradient-to-br from-blue-500/10 to-purple-500/10 rounded-lg border border-blue-200/30">
                  <Settings className="w-5 h-5 text-primary" />
                </div>
                <div className="text-left">
                  <div className="font-semibold text-base">{category.name}</div>
                  <div className="text-sm text-muted-foreground font-normal">{category.description}</div>
                </div>
              </div>
            </AccordionTrigger>
            <AccordionContent className="px-6 pb-6 pt-2">
              <div className="space-y-6">
                {category.settings.map(setting => (
                  <div key={setting.key} className="pb-4 border-b last:border-b-0 last:pb-0">
                    {renderSetting(setting)}
                  </div>
                ))}
              </div>
            </AccordionContent>
          </AccordionItem>
        ))}
      </Accordion>

      {/* Reset to Defaults */}
      <Card className="border-red-200/50">
        <CardHeader>
          <CardTitle className="text-red-600">Danger Zone</CardTitle>
          <CardDescription>
            Reset all configuration values to their defaults. This will affect the running application.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Button
            variant="destructive"
            onClick={resetToDefaults}
            disabled={saving}
          >
            <RotateCcw className="w-4 h-4 mr-2" />
            Reset All to Defaults
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
