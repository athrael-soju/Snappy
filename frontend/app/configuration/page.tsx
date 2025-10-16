"use client";

import "@/lib/api/client";
import { useConfigurationPanel } from "@/lib/hooks/use-configuration-panel";
import { 
  Settings, 
  Save, 
  RotateCcw, 
  AlertCircle, 
  CheckCircle2,
  Loader2,
  Sparkles,
  Zap,
  Info,
  Lock,
  Hash,
  ToggleLeft,
  List
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

export default function ConfigurationPage() {
  const {
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
    optimizeForSystem,
    handleValueChange,
    isSettingVisible,
  } = useConfigurationPanel();

  if (loading && !schema) {
    return (
      <div className="relative flex h-full min-h-full flex-col overflow-hidden">
        <div className="flex h-full flex-1 flex-col items-center justify-center px-4 py-6">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
          <p className="mt-3 text-sm text-muted-foreground">Loading configuration...</p>
        </div>
      </div>
    );
  }

  if (!schema) {
    return (
      <div className="relative flex h-full min-h-full flex-col overflow-hidden">
        <div className="flex h-full flex-1 flex-col items-center justify-center px-4 py-6">
          <AlertCircle className="h-12 w-12 text-muted-foreground/50" />
          <h1 className="mt-3 text-xl font-bold">Configuration Unavailable</h1>
          <p className="mt-2 text-center text-sm text-muted-foreground">
            Configuration data could not be loaded. Check that the API is reachable.
          </p>
        </div>
      </div>
    );
  }

  const categories = Object.entries(schema).sort(([, a], [, b]) => a.order - b.order);
  const activeCategory = categories.find(([key]) => key === activeTab) ?? categories[0];
  const activeKey = activeCategory?.[0] ?? activeTab;
  const activeContent = activeCategory?.[1];

  return (
    <div className="relative flex h-full min-h-full flex-col overflow-hidden">
      <div className="flex h-full flex-1 flex-col overflow-hidden px-4 py-6 sm:px-6 lg:px-8">
        <div className="mx-auto flex h-full w-full max-w-5xl flex-col space-y-4">
          {/* Header Section */}
          <div className="shrink-0 space-y-2 text-center">
            <h1 className="text-2xl font-bold tracking-tight sm:text-3xl lg:text-4xl">
              <span className="bg-gradient-to-br from-foreground via-foreground to-foreground/70 bg-clip-text text-transparent">
                System
              </span>
              {" "}
              <span className="bg-gradient-to-r from-orange-500 via-amber-500 to-orange-500 bg-clip-text text-transparent">
                Configuration
              </span>
            </h1>
            
            <p className="mx-auto max-w-2xl text-xs leading-relaxed text-muted-foreground sm:text-sm">
              Edit backend settings directly. Inputs mirror the OpenAPI schema and save values individually.
            </p>
            
            {error && (
              <div className="mx-auto flex max-w-2xl items-center justify-center gap-2 rounded-lg bg-red-500/10 px-4 py-2 text-sm font-medium text-red-600 dark:text-red-400">
                <AlertCircle className="h-4 w-4" />
                {error}
              </div>
            )}
          </div>

          {/* Controls & Stats */}
          <div className="shrink-0 space-y-3 rounded-xl border border-border/50 bg-card/50 p-4 backdrop-blur-sm">
            <div className="flex flex-wrap items-center gap-3">
              <div className="flex min-w-0 flex-1 items-center gap-2">
                <Settings className="h-4 w-4 shrink-0 text-muted-foreground" />
                <select
                  value={activeKey}
                  onChange={(event) => setActiveTab(event.target.value)}
                  className="min-w-0 flex-1 rounded-lg border border-border/50 bg-background px-3 py-2 text-sm outline-none transition-all focus:border-primary/50 focus:ring-2 focus:ring-primary/20"
                >
                  {categories.map(([key, category]) => (
                    <option key={key} value={key}>
                      {category.name}
                    </option>
                  ))}
                </select>
              </div>

              <Button
                type="button"
                onClick={optimizeForSystem}
                disabled={saving}
                variant="outline"
                size="sm"
                className="gap-2 rounded-full"
              >
                <Zap className="h-4 w-4" />
                <span className="hidden sm:inline">Optimize</span>
              </Button>
              
              <Button
                type="button"
                onClick={resetToDefaults}
                disabled={saving}
                variant="outline"
                size="sm"
                className="gap-2 rounded-full"
              >
                <RotateCcw className="h-4 w-4" />
                <span className="hidden sm:inline">Reset All</span>
              </Button>
            </div>
            
            <div className="flex flex-wrap items-center justify-center gap-2">
              <Badge variant="outline" className="gap-1.5 px-3 py-1">
                <Hash className="h-3 w-3" />
                {configStats.totalSettings} settings
              </Badge>
              <Badge variant="outline" className="gap-1.5 px-3 py-1">
                {configStats.modifiedSettings > 0 ? (
                  <AlertCircle className="h-3 w-3 text-orange-500" />
                ) : (
                  <CheckCircle2 className="h-3 w-3 text-green-500" />
                )}
                {configStats.modifiedSettings} modified
              </Badge>
              <Badge variant="outline" className="gap-1.5 px-3 py-1">
                <Info className="h-3 w-3" />
                {configStats.currentMode}
              </Badge>
              {configStats.enabledFeatures.length > 0 && (
                <Badge variant="secondary" className="gap-1.5 px-3 py-1">
                  <Sparkles className="h-3 w-3" />
                  {configStats.enabledFeatures.join(", ")}
                </Badge>
              )}
              {lastSaved && (
                <Badge variant="outline" className="gap-1.5 px-3 py-1 text-xs">
                  Last saved: {lastSaved.toLocaleTimeString()}
                </Badge>
              )}
            </div>
          </div>

          {/* Settings Section */}
          {activeContent && (
            <div className="flex min-h-0 flex-1 flex-col rounded-xl border border-border/50 bg-card/30 p-4 backdrop-blur-sm">
              <div className="mb-4 shrink-0 space-y-1">
                <div className="flex items-center gap-2">
                  <Settings className="h-5 w-5 text-primary" />
                  <h2 className="text-lg font-bold">{activeContent.name}</h2>
                </div>
                <p className="text-xs text-muted-foreground">{activeContent.description}</p>
              </div>

              <div className="min-h-0 flex-1 space-y-3 overflow-y-auto">
            {activeContent.settings
              .filter((setting) => isSettingVisible(setting))
              .map((setting) => {
                const currentValue = values[setting.key] ?? setting.default;

                if (setting.type === "boolean") {
                  return (
                    <article key={setting.key} className="group rounded-xl border border-border/50 bg-card/50 p-3 backdrop-blur-sm transition-all hover:border-primary/50">
                      <label className="flex cursor-pointer items-start gap-3">
                        <div className="flex h-5 w-5 shrink-0 items-center justify-center">
                          <input
                            type="checkbox"
                            checked={(currentValue || "").toLowerCase() === "true"}
                            onChange={(event) => handleValueChange(setting.key, event.target.checked ? "True" : "False")}
                            disabled={saving}
                            className="h-4 w-4 rounded border-border/50 text-primary focus:ring-2 focus:ring-primary/20"
                          />
                        </div>
                        <div className="min-w-0 flex-1 space-y-1">
                          <div className="flex items-center gap-2">
                            <ToggleLeft className="h-4 w-4 text-primary" />
                            <span className="text-sm font-bold">{setting.label}</span>
                          </div>
                          <p className="text-xs leading-relaxed text-muted-foreground">{setting.description}</p>
                          {setting.help_text && (
                            <p className="text-xs leading-relaxed text-muted-foreground/80">
                              <Info className="mr-1 inline h-3 w-3" />
                              {setting.help_text}
                            </p>
                          )}
                        </div>
                      </label>
                    </article>
                  );
                }

                if (setting.type === "select" && Array.isArray(setting.options)) {
                  return (
                    <article key={setting.key} className="space-y-2 rounded-xl border border-border/50 bg-card/50 p-3 backdrop-blur-sm transition-all hover:border-primary/50">
                      <label className="flex flex-col gap-2">
                        <div className="flex items-center gap-2">
                          <List className="h-4 w-4 text-primary" />
                          <span className="text-sm font-bold">{setting.label}</span>
                        </div>
                        <select
                          value={currentValue}
                          onChange={(event) => handleValueChange(setting.key, event.target.value)}
                          disabled={saving}
                          className="rounded-lg border border-border/50 bg-background px-3 py-2 text-sm outline-none transition-all focus:border-primary/50 focus:ring-2 focus:ring-primary/20"
                        >
                          {setting.options.map((option) => (
                            <option key={option} value={option}>
                              {option}
                            </option>
                          ))}
                        </select>
                      </label>
                      <p className="text-xs leading-relaxed text-muted-foreground">{setting.description}</p>
                      {setting.help_text && (
                        <p className="text-xs leading-relaxed text-muted-foreground/80">
                          <Info className="mr-1 inline h-3 w-3" />
                          {setting.help_text}
                        </p>
                      )}
                    </article>
                  );
                }

                const inputType = setting.type === "password" ? "password" : setting.type === "number" ? "number" : "text";
                const min = typeof setting.min === "number" ? setting.min : undefined;
                const max = typeof setting.max === "number" ? setting.max : undefined;
                const step = typeof setting.step === "number" ? setting.step : undefined;

                const Icon = setting.type === "password" ? Lock : setting.type === "number" ? Hash : Info;
                
                return (
                  <article key={setting.key} className="space-y-2 rounded-xl border border-border/50 bg-card/50 p-3 backdrop-blur-sm transition-all hover:border-primary/50">
                    <label className="flex flex-col gap-2">
                      <div className="flex items-center gap-2">
                        <Icon className="h-4 w-4 text-primary" />
                        <span className="text-sm font-bold">{setting.label}</span>
                      </div>
                      <input
                        type={inputType}
                        value={currentValue}
                        onChange={(event) => handleValueChange(setting.key, event.target.value)}
                        disabled={saving}
                        min={min}
                        max={max}
                        step={step}
                        className="rounded-lg border border-border/50 bg-background px-3 py-2 text-sm outline-none transition-all focus:border-primary/50 focus:ring-2 focus:ring-primary/20"
                      />
                    </label>
                    <p className="text-xs leading-relaxed text-muted-foreground">{setting.description}</p>
                    {setting.help_text && (
                      <p className="text-xs leading-relaxed text-muted-foreground/80">
                        <Info className="mr-1 inline h-3 w-3" />
                        {setting.help_text}
                      </p>
                    )}
                    {setting.depends_on && (
                      <Badge variant="outline" className="gap-1.5 text-xs">
                        <AlertCircle className="h-3 w-3" />
                        Visible when {setting.depends_on.key} = {setting.depends_on.value ? "True" : "False"}
                      </Badge>
                    )}
                  </article>
                );
              })}
              </div>

              <div className="mt-4 flex shrink-0 flex-wrap gap-3">
                <Button
                  type="button"
                  onClick={() => resetSection(activeKey)}
                  disabled={saving}
                  variant="outline"
                  size="sm"
                  className="gap-2 rounded-full"
                >
                  <RotateCcw className="h-4 w-4" />
                  Reset Section
                </Button>
              </div>
            </div>
          )}

          {/* Footer Actions */}
          <div className="shrink-0 rounded-xl border border-border/50 bg-card/50 p-4 backdrop-blur-sm">
            <div className="flex flex-wrap items-center gap-3">
              <Button
                type="button"
                onClick={saveChanges}
                disabled={!hasChanges || saving}
                size="default"
                className="gap-2 rounded-full shadow-lg shadow-primary/20"
              >
                {saving ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Saving...
                  </>
                ) : (
                  <>
                    <Save className="h-4 w-4" />
                    Save Changes
                  </>
                )}
              </Button>
              
              <Button
                type="button"
                onClick={resetChanges}
                disabled={!hasChanges || saving}
                variant="outline"
                size="default"
                className="gap-2 rounded-full"
              >
                <RotateCcw className="h-4 w-4" />
                Discard
              </Button>
              
              {!hasChanges && (
                <Badge variant="secondary" className="gap-1.5">
                  <CheckCircle2 className="h-3 w-3" />
                  No unsaved changes
                </Badge>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
