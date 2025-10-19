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
  History,
  Undo2,
  Trash2,
} from "lucide-react";
import { AppButton } from "@/components/app-button";
import { Badge } from "@/components/ui/badge";
import { InfoTooltip } from "@/components/info-tooltip";
import { RoutePageShell } from "@/components/route-page-shell";
import { Switch } from "@/components/ui/switch";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import Loading from "../loading";

const SETTING_OVERRIDES: Record<
  string,
  {
    description?: string;
    helpText?: string;
  }
> = {
  MINIO_WORKERS: {
    description: "Number of concurrent upload workers (auto-sized)",
    helpText:
      "Vultr auto-derives this from available CPU cores and pipeline concurrency. Override only if you need to cap or expand throughput manually.",
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
  const draftCount = storedDraftKeys.length;
  const draftCountLabel = draftCount === 1 ? "setting" : "settings";
  const draftUpdatedLabel = storedDraftUpdatedAt ? storedDraftUpdatedAt.toLocaleString() : null;

  const heroMeta = (
    <>
      <span className="inline-flex items-center gap-1 rounded-full border border-white/25 bg-white/10 px-3 py-1 text-sm font-medium text-white backdrop-blur">
        <Hash className="size-icon-3xs" />
        {configStats.totalSettings} settings
      </span>
      <span className="inline-flex items-center gap-1 rounded-full border border-white/25 bg-white/10 px-3 py-1 text-sm font-medium text-white backdrop-blur">
        {configStats.modifiedSettings > 0 ? (
          <AlertCircle className="size-icon-3xs text-amber-200" />
        ) : (
          <CheckCircle2 className="size-icon-3xs text-emerald-200" />
        )}
        {configStats.modifiedSettings} modified
      </span>
      <span className="inline-flex items-center gap-1 rounded-full border border-white/25 bg-white/10 px-3 py-1 text-sm font-medium text-white backdrop-blur capitalize">
        <Info className="size-icon-3xs" />
        {configStats.currentMode}
      </span>
      {lastSaved && (
        <span className="inline-flex items-center gap-1 rounded-full border border-white/25 bg-white/10 px-3 py-1 text-sm font-medium text-white backdrop-blur">
          <History className="size-icon-3xs" />
          Last saved {lastSaved.toLocaleTimeString()}
        </span>
      )}
    </>
  );

  const heroActions = (
    <>
      <AppButton
        type="button"
        onClick={() => void saveChanges()}
        disabled={!hasChanges || saving}
        variant="primary"
        size="sm"
        className="rounded-[var(--radius-button)] px-5"
      >
        {saving ? (
          <>
            <Loader2 className="size-icon-xs animate-spin" />
            Saving...
          </>
        ) : (
          <>
            <Save className="size-icon-xs" />
            Save changes
          </>
        )}
      </AppButton>
      <AppButton
        type="button"
        onClick={() => resetToDefaults()}
        disabled={saving}
        variant="outline"
        size="sm"
        className="rounded-[var(--radius-button)]"
      >
        <RotateCcw className="size-icon-xs" />
        Reset defaults
      </AppButton>
    </>
  );

  return (
    <RoutePageShell
      eyebrow="Operations"
      title="System Configuration"
      description="Review and adjust backend behaviour without leaving the app. Save changes section by section when you are ready."
      actions={heroActions}
      meta={heroMeta}
    >
      <motion.div
        className="mx-auto flex w-full max-w-5xl flex-col space-y-4"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, ease: "easeOut" }}
      >
        {error && (
          <div className="mx-auto flex max-w-2xl items-center justify-center gap-2 rounded-lg border border-destructive/40 bg-destructive/10 px-4 py-2 text-body-sm font-medium text-destructive">
            <AlertCircle className="size-icon-xs" />
            {error}
          </div>
        )}

        <AnimatePresence>
          {hasStoredDraft && (
            <motion.div
              key="stored-draft-banner"
              initial={{ opacity: 0, y: -6 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -6 }}
              transition={{ duration: 0.2 }}
              className="mx-auto flex w-full max-w-3xl flex-col gap-3 rounded-2xl border border-amber-200/40 bg-amber-100/30 p-4 text-amber-900 shadow-sm backdrop-blur-sm dark:border-amber-500/40 dark:bg-amber-400/10 dark:text-amber-50"
            >
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <div className="flex items-start gap-3">
                  <History className="mt-0.5 size-icon-sm shrink-0 text-amber-500 dark:text-amber-300" />
                  <div className="space-y-1">
                    <p className="text-body-sm font-semibold">Local draft available</p>
                    <p className="text-body-xs text-amber-800/80 dark:text-amber-100/80">
                      {draftCount} {draftCountLabel} differ from the server.
                      {draftUpdatedLabel ? ` Last updated ${draftUpdatedLabel}.` : ""}
                    </p>
                  </div>
                </div>
                <div className="flex flex-wrap items-center gap-2">
                  <AppButton
                    type="button"
                    size="sm"
                    variant="outline"
                    onClick={restoreStoredDraft}
                    disabled={saving}
                  >
                    <Undo2 className="size-icon-2xs" />
                    Review draft
                  </AppButton>
                  <AppButton
                    type="button"
                    size="sm"
                    variant="outline"
                    onClick={discardStoredDraft}
                    disabled={saving}
                  >
                    <Trash2 className="size-icon-2xs" />
                    Discard
                  </AppButton>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        <motion.div
          className="shrink-0 rounded-3xl border border-border/30 bg-card/10 p-5 shadow-sm backdrop-blur-sm"
          initial={{ opacity: 0, scale: 0.97 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.2, duration: 0.3 }}
        >
          <div className="flex flex-col gap-4">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <div className="flex min-w-0 flex-1 flex-col gap-2">
                <div className="flex items-center gap-2 text-muted-foreground">
                  <Settings className="size-icon-sm shrink-0" />
                  <span className="text-body-xs font-semibold uppercase tracking-wide">
                    Configuration sections
                  </span>
                </div>
                <Tabs value={activeKey} onValueChange={setActiveTab} className="w-full">
                  <TabsList className="flex w-full flex-nowrap justify-start gap-2 overflow-x-auto rounded-xl border border-border/30 bg-background/60 p-1 text-body-sm [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
                    {categories.map(([key, category]) => (
                      <TabsTrigger
                        key={key}
                        value={key}
                        className="grow-0 shrink-0 basis-auto whitespace-nowrap px-3 py-1 text-body-sm font-medium data-[state=active]:bg-primary/10 data-[state=active]:text-primary"
                      >
                        {category.name}
                      </TabsTrigger>
                    ))}
                  </TabsList>
                </Tabs>
              </div>
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
              <span className="inline-flex items-center gap-1 rounded-lg border border-border/30 bg-background/70 px-2.5 py-1 capitalize">
                <Info className="size-icon-3xs" />
                {configStats.currentMode}
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
                        const override = SETTING_OVERRIDES[setting.key] ?? {};
                        const description = override.description ?? setting.description;
                        const helpText = override.helpText ?? setting.help_text;

                        const isDependent = !!setting.depends_on;
                        const articleClass = isDependent
                          ? "group relative ml-4 rounded-2xl border border-border/25 bg-background/60 p-4 shadow-sm sm:ml-6 before:absolute before:left-0 before:top-4 before:h-[calc(100%-2rem)] before:w-px before:-translate-x-3 before:rounded-full before:bg-primary/40"
                          : "group rounded-2xl border border-border/25 bg-background/60 p-4 shadow-sm";

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
                            >
                              <label className="flex flex-col gap-2 touch-manipulation">
                                <div className="flex items-center gap-2">
                                  <List className="size-icon-xs text-primary" />
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
                                  className="input"
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
                          >
                            <label className="flex flex-col gap-2 touch-manipulation">
                              <div className="flex items-center gap-2">
                                <Icon className="size-icon-xs text-primary" />
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
                                className="input"
                              />
                            </label>
                            {setting.depends_on && (
                              <Badge variant="outline" className="w-fit gap-1.5 text-body-xs">
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
            className="shrink-0 rounded-3xl border border-border/30 bg-card/10 p-5 shadow-sm backdrop-blur-sm"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3, duration: 0.3 }}
          >
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <div className="flex flex-wrap items-center gap-3">
                <AppButton
                  type="button"
                  onClick={saveChanges}
                  disabled={!hasChanges || saving}
                  variant="cta"
                  size="lg"
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
                </AppButton>

                <AppButton
                  type="button"
                  onClick={resetChanges}
                  disabled={!hasChanges || saving}
                  variant="outline"
                  size="lg"
                >
                  <RotateCcw className="size-icon-xs" />
                  Discard
                </AppButton>

                <AppButton
                  type="button"
                  onClick={() => resetSection(activeKey)}
                  disabled={saving}
                  variant="ghost"
                  size="lg"
                >
                  <RotateCcw className="size-icon-xs" />
                  Reset section
                </AppButton>
              </div>

              <div className="flex items-center gap-2 text-body-sm text-muted-foreground">
                {hasChanges ? (
                  <span className="inline-flex items-center gap-1">
                    <AlertCircle className="size-icon-3xs text-orange-500" />
                    Unsaved edits
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1">
                    <CheckCircle2 className="size-icon-3xs text-emerald-400" />
                    No unsaved changes
                  </span>
                )}
              </div>
            </div>
          </motion.div>
      </motion.div>
    </RoutePageShell>
  );
}
