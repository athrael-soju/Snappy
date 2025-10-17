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
import { Tooltip, TooltipTrigger, TooltipContent } from "@/components/ui/tooltip";
import { Switch } from "@/components/ui/switch";
import { ScrollArea } from "@/components/ui/scroll-area";

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

  const categories = Object.entries(schema).sort(([, a], [, b]) => a.order - b.order).filter(([key]) => !schema[key].ui_hidden);
  const activeCategory = categories.find(([key]) => key === activeTab) ?? categories[0];
  const activeKey = activeCategory?.[0] ?? activeTab;
  const activeContent = activeCategory?.[1];

  return (
    <div className="relative flex h-full min-h-full flex-col overflow-hidden">
      <div className="flex h-full flex-1 flex-col overflow-hidden px-4 py-6 sm:px-6 lg:px-8">
        <div className="mx-auto flex h-full w-full max-w-5xl flex-col space-y-4">
          {/* Header Section */}
          <div className="shrink-0 space-y-2 text-center">
            <h1 className="text-xl font-bold tracking-tight sm:text-2xl lg:text-3xl">
              <span className="bg-gradient-to-br from-foreground via-foreground to-foreground/70 bg-clip-text text-transparent">
                System
              </span>
              {" "}
              <span className="bg-gradient-to-r from-chart-4 via-chart-3 to-chart-4 bg-clip-text text-transparent">
                Configuration
              </span>
            </h1>
            
            <p className="mx-auto max-w-2xl text-xs leading-relaxed text-muted-foreground">
              Edit backend settings directly. Inputs mirror the OpenAPI schema and save values individually.
            </p>
            
            {error && (
              <div className="mx-auto flex max-w-2xl items-center justify-center gap-2 rounded-lg bg-destructive/10 px-4 py-2 text-sm font-medium text-destructive">
                <AlertCircle className="h-4 w-4" />
                {error}
              </div>
            )}
          </div>

          {/* Controls & Stats */}
          <div className="shrink-0 space-y-3 rounded-2xl border border-border/40 bg-gradient-to-br from-card/30 to-card/50 p-4 backdrop-blur-sm">
            <div className="flex flex-wrap items-center gap-3">
              <div className="flex min-w-0 flex-1 items-center gap-2">
                <Settings className="h-4 w-4 shrink-0 text-muted-foreground" />
                <select
                  value={activeKey}
                  onChange={(event) => setActiveTab(event.target.value)}
                  className="min-w-0 flex-1 rounded-xl border border-border/40 bg-background/50 px-3 py-2 text-sm outline-none transition-all focus:border-primary/50 focus:bg-background focus:ring-2 focus:ring-primary/20"
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
            <div className="flex min-h-0 flex-1 flex-col rounded-2xl border border-border/40 bg-gradient-to-br from-card/20 to-card/40 p-4 backdrop-blur-sm">
              <div className="mb-4 shrink-0">
                <div className="flex items-center gap-2">
                  <Settings className="h-5 w-5 text-primary" />
                  <h2 className="text-lg font-bold">{activeContent.name}</h2>
                  {activeContent.description && (
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Info className="h-4 w-4 text-muted-foreground hover:text-foreground transition-colors" />
                      </TooltipTrigger>
                      <TooltipContent className="max-w-sm">
                        <p>{activeContent.description}</p>
                      </TooltipContent>
                    </Tooltip>
                  )}
                </div>
              </div>

              <ScrollArea className="min-h-0 flex-1">
                <div className="space-y-3 pr-4">
            {activeContent.settings
              .filter((setting) => isSettingVisible(setting))
              .map((setting) => {
                const currentValue = values[setting.key] ?? setting.default;

                const isDependent = !!setting.depends_on;
                const articleClass = isDependent 
                  ? "group ml-6 rounded-2xl border border-border/40 border-l-4 border-l-primary/30 bg-gradient-to-br from-card/30 to-card/50 p-4 backdrop-blur-sm transition-all hover:border-border/60 hover:border-l-primary/50 hover:shadow-sm sm:ml-8"
                  : "group rounded-2xl border border-border/40 bg-gradient-to-br from-card/30 to-card/50 p-4 backdrop-blur-sm transition-all hover:border-border/60 hover:shadow-sm";

                if (setting.type === "boolean") {
                  return (
                    <article key={setting.key} className={articleClass}>
                      <div className="flex items-center justify-between gap-4 min-h-[44px]">
                        <div className="flex min-w-0 flex-1 items-center gap-2">
                          <ToggleLeft className="h-4 w-4 shrink-0 text-primary" />
                          <span className="text-sm font-semibold">{setting.label}</span>
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <button type="button" className="inline-flex shrink-0">
                                <Info className="h-3.5 w-3.5 text-muted-foreground hover:text-foreground transition-colors" />
                              </button>
                            </TooltipTrigger>
                            <TooltipContent className="max-w-xs">
                              <p>{setting.description}</p>
                              {setting.help_text && (
                                <p className="mt-1 text-xs opacity-80">{setting.help_text}</p>
                              )}
                            </TooltipContent>
                          </Tooltip>
                        </div>
                        <Switch
                          checked={(currentValue || "").toLowerCase() === "true"}
                          onCheckedChange={(checked) => handleValueChange(setting.key, checked ? "True" : "False")}
                          disabled={saving}
                        />
                      </div>
                    </article>
                  );
                }

                if (setting.type === "select" && Array.isArray(setting.options)) {
                  return (
                    <article key={setting.key} className={`space-y-2 ${articleClass}`}>
                      <label className="flex flex-col gap-2 touch-manipulation">
                        <div className="flex items-center gap-2">
                          <List className="h-4 w-4 text-primary" />
                          <span className="text-sm font-semibold">{setting.label}</span>
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <button type="button" className="inline-flex">
                                <Info className="h-3.5 w-3.5 text-muted-foreground hover:text-foreground transition-colors" />
                              </button>
                            </TooltipTrigger>
                            <TooltipContent className="max-w-xs">
                              <p>{setting.description}</p>
                              {setting.help_text && (
                                <p className="mt-1 text-xs opacity-80">{setting.help_text}</p>
                              )}
                            </TooltipContent>
                          </Tooltip>
                        </div>
                        <select
                          value={currentValue}
                          onChange={(event) => handleValueChange(setting.key, event.target.value)}
                          disabled={saving}
                          className="w-full rounded-xl border border-border/40 bg-background/50 px-3 py-2.5 text-sm outline-none transition-all focus:border-primary/50 focus:bg-background focus:ring-2 focus:ring-primary/20"
                        >
                          {setting.options.map((option) => (
                            <option key={option} value={option}>
                              {option}
                            </option>
                          ))}
                        </select>
                      </label>
                    </article>
                  );
                }

                const inputType = setting.type === "password" ? "password" : setting.type === "number" ? "number" : "text";
                const min = typeof setting.min === "number" ? setting.min : undefined;
                const max = typeof setting.max === "number" ? setting.max : undefined;
                const step = typeof setting.step === "number" ? setting.step : undefined;

                const Icon = setting.type === "password" ? Lock : setting.type === "number" ? Hash : Info;
                
                return (
                  <article key={setting.key} className={`space-y-2 ${articleClass}`}>
                    <label className="flex flex-col gap-2 touch-manipulation">
                      <div className="flex items-center gap-2">
                        <Icon className="h-4 w-4 text-primary" />
                        <span className="text-sm font-semibold">{setting.label}</span>
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <button type="button" className="inline-flex">
                              <Info className="h-3.5 w-3.5 text-muted-foreground hover:text-foreground transition-colors" />
                            </button>
                          </TooltipTrigger>
                          <TooltipContent className="max-w-xs">
                            <p>{setting.description}</p>
                            {setting.help_text && (
                              <p className="mt-1 text-xs opacity-80">{setting.help_text}</p>
                            )}
                          </TooltipContent>
                        </Tooltip>
                      </div>
                      <input
                        type={inputType}
                        value={currentValue}
                        onChange={(event) => handleValueChange(setting.key, event.target.value)}
                        disabled={saving}
                        min={min}
                        max={max}
                        step={step}
                        className="w-full rounded-xl border border-border/40 bg-background/50 px-3 py-2.5 text-sm outline-none transition-all focus:border-primary/50 focus:bg-background focus:ring-2 focus:ring-primary/20"
                      />
                    </label>
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
              </ScrollArea>
            </div>
          )}

          {/* Footer Actions */}
          <div className="shrink-0 rounded-2xl border border-border/40 bg-gradient-to-br from-card/30 to-card/50 p-4 backdrop-blur-sm">
            <div className="flex flex-wrap items-center justify-between gap-3">
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
              
              <Button
                type="button"
                onClick={() => resetSection(activeKey)}
                disabled={saving}
                variant="outline"
                size="sm"
                className="gap-2 rounded-full"
              >
                <RotateCcw className="h-4 w-4" />
                <span className="hidden sm:inline">Reset Section</span>
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
