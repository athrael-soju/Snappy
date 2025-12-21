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
  AlertTriangle,
} from "lucide-react";
import { AppButton } from "@/components/app-button";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";
import { InfoTooltip } from "@/components/info-tooltip";
import { PageHeader } from "@/components/page-header";
import { Switch } from "@/components/ui/switch";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import Loading from "../loading";

const SETTING_OVERRIDES: Record<
  string,
  {
    description?: string;
    helpText?: string;
  }
> = {
  STORAGE_WORKERS: {
    description: "Number of concurrent upload workers (auto-sized)",
    helpText:
      "Snappy derives this from available CPU cores and pipeline concurrency. Override only if you need to cap or expand throughput manually.",
  },
};

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
    pendingConfirmation,
    confirmValueChange,
    cancelValueChange,
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
            className="shrink-0"
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1, duration: 0.3 }}
          >
            <PageHeader
              align="center"
              title={
                <>
                  <span className="bg-gradient-to-br from-foreground via-foreground to-foreground/70 bg-clip-text text-transparent">
                    System
                  </span>{" "}
                  <span className="bg-gradient-to-r from-chart-4 via-chart-3 to-chart-4 bg-clip-text text-transparent">
                    Configuration
                  </span>
                </>
              }
              description="Review and adjust backend behaviour without leaving the app. Save changes section by section when you are ready."
            />
            {error && (
              <div className="mx-auto flex max-w-2xl items-center justify-center gap-2 rounded-lg bg-destructive/10 px-4 py-2 text-body-sm font-medium text-destructive">
                <AlertCircle className="size-icon-xs" />
                {error}
              </div>
            )}
          </motion.div>

          {/* Controls & Stats */}
          <motion.div
            className="shrink-0 rounded-3xl border border-border/30 bg-card/10 p-5 shadow-sm backdrop-blur-sm"
            initial={{ opacity: 0, scale: 0.97 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.2, duration: 0.3 }}
          >
            <div className="flex flex-col gap-4">
              <div className="flex min-w-0 flex-1 flex-col gap-2">
                <div className="flex items-center gap-2 text-muted-foreground">
                  <Settings className="size-icon-sm shrink-0" />
                  <span className="text-body-xs font-semibold uppercase tracking-wide">
                    Configuration sections
                  </span>
                </div>
                <Tabs value={activeKey} onValueChange={setActiveTab} className="w-full">
                  <TabsList className="grid w-full grid-cols-[repeat(auto-fit,minmax(120px,1fr))] gap-2 rounded-xl border border-border/30 bg-background/60 p-1 text-body-sm">
                    {categories.map(([key, category]) => (
                      <TabsTrigger
                        key={key}
                        value={key}
                        className="whitespace-nowrap px-3 py-1 text-body-sm font-medium data-[state=active]:bg-primary/10 data-[state=active]:text-primary"
                      >
                        {category.name}
                      </TabsTrigger>
                    ))}
                  </TabsList>
                </Tabs>
              </div>

              <div className="flex flex-wrap items-center gap-3 text-body-sm text-muted-foreground">
                <span className="inline-flex items-center gap-1 rounded-lg border border-border/30 bg-background/70 px-2.5 py-1">
                  <Hash className="size-icon-3xs" />
                  {configStats.totalSettings} settings
                </span>
                <span className="inline-flex items-center gap-1 rounded-lg border border-border/30 bg-background/70 px-2.5 py-1">
                  {configStats.modifiedSettings > 0 ? (
                    <AlertCircle className="size-icon-3xs text-orange-500" />
                  ) : (
                    <CheckCircle2 className="size-icon-3xs text-emerald-400" />
                  )}
                  {configStats.modifiedSettings} modified
                </span>
                {configStats.enabledFeatures.length > 0 && (
                  <span className="inline-flex items-center gap-1 rounded-lg border border-border/30 bg-background/70 px-2.5 py-1">
                    <Sparkles className="size-icon-3xs text-primary" />
                    {configStats.enabledFeatures.join(", ")}
                  </span>
                )}
                {lastSaved && (
                  <span className="ml-auto inline-flex items-center gap-1 rounded-lg border border-border/30 bg-background/70 px-2.5 py-1 text-body-xs">
                    Last saved {lastSaved.toLocaleTimeString()}
                  </span>
                )}
              </div>
            </div>
          </motion.div>

          {/* Settings Section */}
          <AnimatePresence mode="wait">
            {activeContent && (
              <motion.div
                key={activeKey}
                className="flex min-h-0 flex-1 flex-col rounded-3xl border border-border/25 bg-card/15 p-6 shadow-sm backdrop-blur-sm"
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
                      <InfoTooltip description={activeContent.description} />
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
                        const currentValueBool = (currentValue || "").toLowerCase() === "true";
                        const override = SETTING_OVERRIDES[setting.key] ?? {};
                        const description = override.description ?? setting.description;
                        const helpText = override.helpText ?? setting.help_text;
                        const disabled = Boolean(setting.ui_disabled);

                        const isDependent = !!setting.depends_on;
                        const indentLevel = setting.ui_indent_level ?? 0;

                        // Base classes for all articles
                        const baseArticleClass = "group rounded-2xl border border-border/25 bg-background/60 p-4 shadow-sm";

                        // Dependent setting classes with connector line
                        const dependentClasses = "relative before:absolute before:left-0 before:top-4 before:h-[calc(100%-2rem)] before:w-px before:-translate-x-3 before:rounded-full before:bg-primary/40";

                        // Indent level classes - using safe Tailwind classes
                        const indentClasses = indentLevel > 0
                          ? indentLevel === 1
                            ? "ml-8 sm:ml-12"
                            : indentLevel === 2
                              ? "ml-16 sm:ml-20"
                              : "ml-24 sm:ml-28"
                          : "ml-4 sm:ml-6";

                        const articleClass = isDependent
                          ? `${baseArticleClass} ${dependentClasses} ${indentClasses}`
                          : baseArticleClass;

                        if (setting.type === "boolean") {
                          return (
                            <motion.article
                              key={setting.key}
                              className={articleClass}
                              initial={{ opacity: 0, y: 10 }}
                              animate={{ opacity: 1, y: 0 }}
                              transition={{ duration: 0.2 }}
                            >
                              <div className="flex items-center justify-between gap-4 min-h-[48px] touch-manipulation">
                                <div className="flex min-w-0 flex-1 items-center gap-2">
                                  <ToggleLeft className="size-icon-xs shrink-0 text-primary" />
                                  <span className="text-body-sm font-semibold">{setting.label}</span>
                                  <InfoTooltip
                                    title={description}
                                    description={helpText}
                                    triggerClassName="shrink-0"
                                  />
                                </div>
                                <Switch
                                  checked={currentValueBool}
                                  onCheckedChange={(checked) => handleValueChange(setting.key, checked ? "True" : "False")}
                                  disabled={saving || (disabled && !currentValueBool)}
                                />
                              </div>
                            </motion.article>
                          );
                        }

                        if (setting.type === "multiselect") {
                          const optionEntries =
                            setting.options?.map((option) => {
                              const trimmed = option.trim();
                              return {
                                raw: trimmed,
                                normalized: trimmed.toLowerCase(),
                              };
                            }) ?? [];
                          const selectedValues = new Set(
                            (currentValue || "")
                              .split(",")
                              .map((value) => value.trim().toLowerCase())
                              .filter(Boolean)
                          );
                          const handleToggle = (optionRaw: string, nextState: boolean) => {
                            const normalized = optionRaw.trim().toLowerCase();
                            const nextSelected = new Set(selectedValues);
                            if (nextState) {
                              nextSelected.add(normalized);
                            } else {
                              if (nextSelected.has(normalized) && nextSelected.size <= 1) {
                                return;
                              }
                              nextSelected.delete(normalized);
                            }
                            const nextValue = optionEntries
                              .filter(({ normalized: opt }) => nextSelected.has(opt))
                              .map(({ raw }) => raw)
                              .join(",");
                            handleValueChange(setting.key, nextValue);
                          };

                          const selectedBadges = optionEntries
                            .filter(({ normalized }) => selectedValues.has(normalized))
                            .map(({ raw }) => raw.toUpperCase());

                          return (
                            <motion.article
                              key={setting.key}
                              className={articleClass}
                              initial={{ opacity: 0, y: 10 }}
                              animate={{ opacity: 1, y: 0 }}
                              transition={{ duration: 0.2 }}
                            >
                              <div className="flex flex-col gap-2">
                                <div className="flex items-center justify-between gap-4 min-h-[48px] touch-manipulation">
                                  <div className="flex min-w-0 flex-1 items-center gap-2">
                                    <List className="size-icon-xs shrink-0 text-primary" />
                                    <span className="text-body-sm font-semibold">{setting.label}</span>
                                    <InfoTooltip
                                      title={description}
                                      description={helpText}
                                      triggerClassName="shrink-0"
                                    />
                                  </div>
                                  <div className="flex flex-wrap items-center justify-end gap-3">
                                    {optionEntries.length === 0 ? (
                                      <span className="text-body-xs text-muted-foreground">
                                        No options configured.
                                      </span>
                                    ) : (
                                      optionEntries.map(({ raw, normalized }) => {
                                        const optionId = `${setting.key}-${normalized}`;
                                        const isChecked = selectedValues.has(normalized);
                                        const labelText = raw.toUpperCase();
                                        return (
                                          <label
                                            key={normalized}
                                            htmlFor={optionId}
                                            className="inline-flex items-center gap-2 text-body-sm font-medium"
                                          >
                                            <Checkbox
                                              id={optionId}
                                              checked={isChecked}
                                              disabled={
                                                saving ||
                                                disabled ||
                                                (isChecked && selectedValues.size <= 1)
                                              }
                                              onCheckedChange={(value) => {
                                                if (value === "indeterminate") return;
                                                handleToggle(raw, Boolean(value));
                                              }}
                                            />
                                            <span>{labelText}</span>
                                          </label>
                                        );
                                      })
                                    )}
                                  </div>
                                </div>
                              </div>
                            </motion.article>
                          );
                        }

                        if (setting.type === "select" && Array.isArray(setting.options)) {
                          return (
                            <motion.article
                              key={setting.key}
                              className={articleClass}
                              initial={{ opacity: 0, y: 10 }}
                              animate={{ opacity: 1, y: 0 }}
                              transition={{ duration: 0.2 }}
                            >
                              <div className="flex items-center justify-between gap-4 min-h-[48px] touch-manipulation">
                                <div className="flex min-w-0 flex-1 items-center gap-2">
                                  <List className="size-icon-xs shrink-0 text-primary" />
                                  <span className="text-body-sm font-semibold">{setting.label}</span>
                                  <InfoTooltip
                                    title={description}
                                    description={helpText}
                                    triggerClassName="shrink-0"
                                  />
                                </div>
                                <select
                                  value={currentValue}
                                  onChange={(event) => handleValueChange(setting.key, event.target.value)}
                                  disabled={saving}
                                  className="w-auto min-w-[120px] max-w-[200px] rounded-lg border border-border/25 bg-background/75 px-3 py-2.5 text-body-sm text-right outline-none transition-colors focus:border-primary/40 focus:bg-background focus:ring-2 focus:ring-primary/15"
                                >
                                  {setting.options.map((option) => (
                                    <option key={option} value={option}>
                                      {option}
                                    </option>
                                  ))}
                                </select>
                              </div>
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
                            className={articleClass}
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ duration: 0.2 }}
                          >
                            <div className="flex items-center justify-between gap-4 min-h-[48px] touch-manipulation">
                              <div className="flex min-w-0 flex-1 items-center gap-2">
                                <Icon className="size-icon-xs shrink-0 text-primary" />
                                <span className="text-body-sm font-semibold">{setting.label}</span>
                                <InfoTooltip
                                  title={description}
                                  description={helpText}
                                  triggerClassName="shrink-0"
                                />
                              </div>
                              <input
                                type={inputType}
                                value={currentValue}
                                onChange={(event) => handleValueChange(setting.key, event.target.value)}
                                disabled={saving}
                                min={min}
                                max={max}
                                step={step}
                                className="w-auto min-w-[120px] max-w-[200px] rounded-lg border border-border/25 bg-background/75 px-3 py-2.5 text-body-sm text-right outline-none transition-colors focus:border-primary/40 focus:bg-background focus:ring-2 focus:ring-primary/15"
                              />
                            </div>
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
            className="shrink-0 rounded-3xl border border-border/30 bg-card/10 p-5 shadow-sm backdrop-blur-sm"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3, duration: 0.3 }}
          >
            <div className="grid w-full grid-cols-4 gap-2 rounded-xl border border-border/30 bg-background/60 p-1">
              <button
                type="button"
                onClick={saveChanges}
                disabled={!hasChanges || saving}
                className="inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-lg px-3 py-2.5 text-body-sm font-medium transition-colors hover:bg-primary/10 hover:text-primary disabled:pointer-events-none disabled:opacity-60 data-[state=active]:bg-primary/10 data-[state=active]:text-primary"
                data-state={hasChanges ? "active" : "inactive"}
              >
                {saving ? (
                  <>
                    <Loader2 className="size-icon-xs animate-spin" />
                    Saving…
                  </>
                ) : (
                  <>
                    <Save className="size-icon-xs" />
                    Save changes
                  </>
                )}
              </button>

              <button
                type="button"
                onClick={resetChanges}
                disabled={!hasChanges || saving}
                className="inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-lg px-3 py-2.5 text-body-sm font-medium transition-colors hover:bg-primary/10 hover:text-primary disabled:pointer-events-none disabled:opacity-60"
              >
                <RotateCcw className="size-icon-xs" />
                Discard
              </button>

              <button
                type="button"
                onClick={() => resetSection(activeKey)}
                disabled={saving}
                className="inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-lg px-3 py-2.5 text-body-sm font-medium transition-colors hover:bg-primary/10 hover:text-primary disabled:pointer-events-none disabled:opacity-60"
              >
                <RotateCcw className="size-icon-xs" />
                Reset section
              </button>

              <button
                type="button"
                onClick={resetToDefaults}
                disabled={false}
                className="inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-lg px-3 py-2.5 text-body-sm font-medium transition-colors hover:bg-primary/10 hover:text-primary disabled:pointer-events-none disabled:opacity-60"
              >
                <RotateCcw className="size-icon-xs" />
                Reset all
              </button>
            </div>
          </motion.div>
        </motion.div>
      </div>

      {/* Confirmation Dialog */}
      <AlertDialog open={!!pendingConfirmation} onOpenChange={(open) => !open && cancelValueChange()}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <div className="flex items-center gap-2">
              <AlertTriangle className="size-icon-md text-orange-500" />
              <AlertDialogTitle>Confirm Configuration Change</AlertDialogTitle>
            </div>
            <AlertDialogDescription className="pt-2">
              {pendingConfirmation?.setting.ui_confirm_message ||
                "This change may affect your existing data. Are you sure you want to continue?"}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel onClick={cancelValueChange}>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={confirmValueChange}>Continue</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
