"use client";

import { motion, AnimatePresence } from "framer-motion";
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
  Info,
  Lock,
  Hash,
  ToggleLeft,
  List,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tooltip, TooltipTrigger, TooltipContent } from "@/components/ui/tooltip";
import { Switch } from "@/components/ui/switch";
import { ScrollArea } from "@/components/ui/scroll-area";
import Loading from "../loading";

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
    handleValueChange,
    isSettingVisible,
  } = useConfigurationPanel();

  if (loading && !schema) {
    return <Loading />;
  }

  if (!schema) {
    return (
      <div className="relative flex h-full min-h-full flex-col overflow-hidden">
        <div className="flex h-full flex-1 flex-col items-center justify-center px-4 py-6">
          <AlertCircle className="size-icon-3xl text-muted-foreground/50" />
          <h1 className="mt-3 text-xl font-bold">Configuration Unavailable</h1>
          <p className="mt-2 text-center text-body-sm text-muted-foreground">
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
        <motion.div 
          className="mx-auto flex h-full w-full max-w-5xl flex-col space-y-4"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, ease: "easeOut" }}
        >
          {/* Header Section */}
          <motion.div 
            className="shrink-0 space-y-2 text-center"
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1, duration: 0.3 }}
          >
            <h1 className="text-xl font-bold tracking-tight sm:text-2xl lg:text-3xl">
              <span className="bg-gradient-to-br from-foreground via-foreground to-foreground/70 bg-clip-text text-transparent">
                System
              </span>
              {" "}
              <span className="bg-gradient-to-r from-chart-4 via-chart-3 to-chart-4 bg-clip-text text-transparent">
                Configuration
              </span>
            </h1>
            
            <p className="mx-auto max-w-2xl text-body-xs leading-relaxed text-muted-foreground">
              Edit backend settings directly. Inputs mirror the OpenAPI schema and save values individually.
            </p>
            
            {error && (
              <div className="mx-auto flex max-w-2xl items-center justify-center gap-2 rounded-lg bg-destructive/10 px-4 py-2 text-body-sm font-medium text-destructive">
                <AlertCircle className="size-icon-xs" />
                {error}
              </div>
            )}
          </motion.div>

          {/* Controls & Stats */}
          <motion.div 
            className="shrink-0 space-y-3 rounded-2xl border border-border/40 bg-gradient-to-br from-card/30 to-card/50 p-4 backdrop-blur-sm"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.2, duration: 0.3 }}
          >
            <div className="flex flex-wrap items-center gap-3">
              <div className="flex min-w-0 flex-1 items-center gap-2">
                <Settings className="size-icon-xs shrink-0 text-muted-foreground" />
                <select
                  value={activeKey}
                  onChange={(event) => setActiveTab(event.target.value)}
                  className="min-w-0 flex-1 rounded-xl border border-border/40 bg-background/50 px-3 py-2 text-body-sm outline-none transition-all focus:border-primary/50 focus:bg-background focus:ring-2 focus:ring-primary/20"
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
                onClick={resetToDefaults}
                disabled={saving}
                variant="outline"
                size="sm"
                className="h-10 gap-2 rounded-full px-4 touch-manipulation"
              >
                <RotateCcw className="size-icon-xs" />
                <span className="hidden sm:inline">Reset All</span>
              </Button>
            </div>
            
            <div className="flex flex-wrap items-center justify-center gap-2">
              <Badge variant="outline" className="gap-1.5 px-3 py-1">
                <Hash className="size-icon-3xs" />
                {configStats.totalSettings} settings
              </Badge>
              <Badge variant="outline" className="gap-1.5 px-3 py-1">
                {configStats.modifiedSettings > 0 ? (
                  <AlertCircle className="size-icon-3xs text-orange-500" />
                ) : (
                  <CheckCircle2 className="size-icon-3xs text-green-500" />
                )}
                {configStats.modifiedSettings} modified
              </Badge>
              <Badge variant="outline" className="gap-1.5 px-3 py-1">
                <Info className="size-icon-3xs" />
                {configStats.currentMode}
              </Badge>
              {configStats.enabledFeatures.length > 0 && (
                <Badge variant="secondary" className="gap-1.5 px-3 py-1">
                  <Sparkles className="size-icon-3xs" />
                  {configStats.enabledFeatures.join(", ")}
                </Badge>
              )}
              {lastSaved && (
                <Badge variant="outline" className="gap-1.5 px-3 py-1 text-body-xs">
                  Last saved: {lastSaved.toLocaleTimeString()}
                </Badge>
              )}
            </div>
          </motion.div>

          {/* Settings Section */}
          <AnimatePresence mode="wait">
            {activeContent && (
              <motion.div 
                key={activeKey}
                className="flex min-h-0 flex-1 flex-col rounded-2xl border border-border/40 bg-gradient-to-br from-card/20 to-card/40 p-4 backdrop-blur-sm"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                transition={{ duration: 0.3 }}
              >
              <div className="mb-4 shrink-0">
                <div className="flex items-center gap-2">
                  <Settings className="size-icon-md text-primary" />
                  <h2 className="text-lg font-bold">{activeContent.name}</h2>
                  {activeContent.description && (
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Info className="size-icon-xs text-muted-foreground hover:text-foreground transition-colors" />
                      </TooltipTrigger>
                      <TooltipContent className="max-w-sm">
                        <p>{activeContent.description}</p>
                      </TooltipContent>
                    </Tooltip>
                  )}
                </div>
              </div>

              <ScrollArea className="min-h-0 flex-1">
                <motion.div 
                  className="space-y-3 pr-4"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: 0.1, duration: 0.3 }}
                >
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
                    <motion.article 
                      key={setting.key} 
                      className={articleClass}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.2 }}
                      whileHover={{ scale: 1.01 }}
                    >
                      <div className="flex items-center justify-between gap-4 min-h-[48px] touch-manipulation">
                        <div className="flex min-w-0 flex-1 items-center gap-2">
                          <ToggleLeft className="size-icon-xs shrink-0 text-primary" />
                          <span className="text-body-sm font-semibold">{setting.label}</span>
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <button type="button" className="inline-flex shrink-0">
                                <Info className="size-icon-2xs text-muted-foreground hover:text-foreground transition-colors" />
                              </button>
                            </TooltipTrigger>
                            <TooltipContent className="max-w-xs">
                              <p>{setting.description}</p>
                              {setting.help_text && (
                                <p className="mt-1 text-body-xs opacity-80">{setting.help_text}</p>
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
                    </motion.article>
                  );
                }

                if (setting.type === "select" && Array.isArray(setting.options)) {
                  return (
                    <motion.article 
                      key={setting.key} 
                      className={`space-y-2 ${articleClass}`}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.2 }}
                      whileHover={{ scale: 1.01 }}
                    >
                      <label className="flex flex-col gap-2 touch-manipulation">
                        <div className="flex items-center gap-2">
                          <List className="size-icon-xs text-primary" />
                          <span className="text-body-sm font-semibold">{setting.label}</span>
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <button type="button" className="inline-flex">
                                <Info className="size-icon-2xs text-muted-foreground hover:text-foreground transition-colors" />
                              </button>
                            </TooltipTrigger>
                            <TooltipContent className="max-w-xs">
                              <p>{setting.description}</p>
                              {setting.help_text && (
                                <p className="mt-1 text-body-xs opacity-80">{setting.help_text}</p>
                              )}
                            </TooltipContent>
                          </Tooltip>
                        </div>
                        <select
                          value={currentValue}
                          onChange={(event) => handleValueChange(setting.key, event.target.value)}
                          disabled={saving}
                          className="w-full rounded-xl border border-border/40 bg-background/50 px-3 py-2.5 text-body-sm outline-none transition-all focus:border-primary/50 focus:bg-background focus:ring-2 focus:ring-primary/20"
                        >
                          {setting.options.map((option) => (
                            <option key={option} value={option}>
                              {option}
                            </option>
                          ))}
                        </select>
                      </label>
                    </motion.article>
                  );
                }

                const inputType = setting.type === "password" ? "password" : setting.type === "number" ? "number" : "text";
                const min = typeof setting.min === "number" ? setting.min : undefined;
                const max = typeof setting.max === "number" ? setting.max : undefined;
                const step = typeof setting.step === "number" ? setting.step : undefined;

                const Icon = setting.type === "password" ? Lock : setting.type === "number" ? Hash : Info;
                
                return (
                  <motion.article 
                    key={setting.key} 
                    className={`space-y-2 ${articleClass}`}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.2 }}
                    whileHover={{ scale: 1.01 }}
                  >
                    <label className="flex flex-col gap-2 touch-manipulation">
                      <div className="flex items-center gap-2">
                        <Icon className="size-icon-xs text-primary" />
                        <span className="text-body-sm font-semibold">{setting.label}</span>
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <button type="button" className="inline-flex">
                              <Info className="size-icon-2xs text-muted-foreground hover:text-foreground transition-colors" />
                            </button>
                          </TooltipTrigger>
                          <TooltipContent className="max-w-xs">
                            <p>{setting.description}</p>
                            {setting.help_text && (
                              <p className="mt-1 text-body-xs opacity-80">{setting.help_text}</p>
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
                        className="w-full rounded-xl border border-border/40 bg-background/50 px-3 py-2.5 text-body-sm outline-none transition-all focus:border-primary/50 focus:bg-background focus:ring-2 focus:ring-primary/20"
                      />
                    </label>
                    {setting.depends_on && (
                      <Badge variant="outline" className="gap-1.5 text-body-xs">
                        <AlertCircle className="size-icon-3xs" />
                        Visible when {setting.depends_on.key} = {setting.depends_on.value ? "True" : "False"}
                      </Badge>
                    )}
                  </motion.article>
                );
              })}
                </motion.div>
              </ScrollArea>
            </motion.div>
          )}
          </AnimatePresence>

          {/* Footer Actions */}
          <motion.div 
            className="shrink-0 rounded-2xl border border-border/40 bg-gradient-to-br from-card/30 to-card/50 p-4 backdrop-blur-sm"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3, duration: 0.3 }}
          >
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div className="flex flex-wrap items-center gap-3">
                <Button
                  type="button"
                  onClick={saveChanges}
                  disabled={!hasChanges || saving}
                  size="default"
                  className="h-11 gap-2 rounded-full px-6 shadow-lg shadow-primary/20 touch-manipulation"
                >
                  {saving ? (
                    <>
                      <Loader2 className="size-icon-xs animate-spin" />
                      Saving...
                    </>
                  ) : (
                    <>
                      <Save className="size-icon-xs" />
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
                  className="h-11 gap-2 rounded-full px-6 touch-manipulation"
                >
                  <RotateCcw className="size-icon-xs" />
                  Discard
                </Button>
                
                {!hasChanges && (
                  <Badge variant="secondary" className="gap-1.5">
                    <CheckCircle2 className="size-icon-3xs" />
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
                className="h-10 gap-2 rounded-full px-4 touch-manipulation"
              >
                <RotateCcw className="size-icon-xs" />
                <span className="hidden sm:inline">Reset Section</span>
              </Button>
            </div>
          </motion.div>
        </motion.div>
      </div>
    </div>
  );
}
