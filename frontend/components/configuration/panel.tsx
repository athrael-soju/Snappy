"use client";

import { useState, forwardRef, useImperativeHandle } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ButtonGroup } from "@/components/ui/button-group";
import { GlassPanel } from "@/components/ui/glass-panel";
import { Separator } from "@/components/ui/separator";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Skeleton } from "@/components/ui/skeleton";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { Settings, RotateCcw, AlertTriangle, Loader2, Sparkles } from "lucide-react";
import { motion } from "framer-motion";
import { ConfigurationTabs } from "@/components/configuration/configuration-tabs";
import { UnsavedChangesBar } from "@/components/configuration/unsaved-changes-bar";
import { SettingRenderer } from "@/components/configuration/setting-renderer";
import { useConfigurationPanel } from "@/lib/hooks/use-configuration-panel";

export type ConfigurationPanelHandle = {
  openResetDialog: () => void;
};

export const ConfigurationPanel = forwardRef<ConfigurationPanelHandle, {}>((_, ref) => {
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
    optimizing,
    saveChanges,
    resetChanges,
    resetSection,
    resetToDefaults,
    optimizeForSystem,
    handleValueChange,
    isSettingVisible,
  } = useConfigurationPanel();

  const [resetDialogOpen, setResetDialogOpen] = useState(false);
  const [resetSectionDialogOpen, setResetSectionDialogOpen] = useState<string | null>(null);

  useImperativeHandle(ref, () => ({
    openResetDialog: () => setResetDialogOpen(true),
  }));

  if (loading && schema) {
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

  if (!schema) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
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
    <div className="flex flex-col h-full gap-4 sm:gap-6">
      {/* Error alert */}
      {error && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Horizontal tabs - centered at top */}
      <div className="flex-shrink-0">
        <ConfigurationTabs
          categories={categoriesToRender}
          activeTab={activeCategoryKey}
          onTabChange={setActiveTab}
        />
      </div>

      {/* Main content area */}
      <div className="flex-1 min-h-0 flex flex-col gap-4 sm:gap-6">
        {/* Action Button Group */}
        <div className="flex-shrink-0">
          <GlassPanel className="p-2">
            <div className="flex w-full gap-2">
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    onClick={optimizeForSystem}
                    disabled={saving || optimizing}
                    className="flex-1 gap-2 text-sm text-primary rounded-xl h-11"
                  >
                    {optimizing ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        <span>Optimizing...</span>
                      </>
                    ) : (
                      <>
                        <Sparkles className="w-4 h-4" />
                        <span>Optimize</span>
                      </>
                    )}
                  </Button>
                </TooltipTrigger>
                <TooltipContent>
                  Detect hardware and apply recommended settings
                </TooltipContent>
              </Tooltip>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    onClick={() => setResetSectionDialogOpen(activeCategoryKey)}
                    disabled={saving}
                    className="flex-1 gap-2 text-sm rounded-xl h-11"
                  >
                    <RotateCcw className="w-4 h-4" />
                    <span>Reset Section</span>
                  </Button>
                </TooltipTrigger>
                <TooltipContent>
                  Reset current section to defaults
                </TooltipContent>
              </Tooltip>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    onClick={() => setResetDialogOpen(true)}
                    disabled={saving}
                    className="flex-1 gap-2 text-sm text-destructive rounded-xl h-11"
                  >
                    <RotateCcw className="w-4 h-4" />
                    <span>Reset All</span>
                  </Button>
                </TooltipTrigger>
                <TooltipContent>
                  Reset all configuration to defaults
                </TooltipContent>
              </Tooltip>
            </div>
          </GlassPanel>
        </div>

        {/* Scrollable content area */}
        <div className="flex-1 min-h-0">
          <ScrollArea className="h-full pr-2">
            <div className="px-1 pb-20 space-y-4">
              {categoriesToRender.map(([categoryKey, category]) => {
                if (activeCategoryKey !== categoryKey) return null;

                // Filter to show only top-level settings (exclude nested children with depends_on)
                const visibleSettings = category.settings.filter(s => isSettingVisible(s) && !s.depends_on);

                return (
                  <motion.div
                    key={categoryKey}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    transition={{ duration: 0.2 }}
                  >
                    <GlassPanel className="p-4 sm:p-6">
                      <CardHeader className="px-0 pt-0 pb-4 sm:pb-6">
                        <div className="flex items-start gap-2 sm:gap-3">
                          <div className="flex size-10 sm:size-12 items-center justify-center rounded-lg bg-primary/10 text-primary flex-shrink-0">
                            <Settings className="w-5 h-5 sm:w-6 sm:h-6" />
                          </div>
                          <div className="min-w-0">
                            <CardTitle className="text-lg sm:text-xl font-semibold">{category.name}</CardTitle>
                            <CardDescription className="mt-1 text-sm sm:text-base">{category.description}</CardDescription>
                          </div>
                        </div>
                      </CardHeader>

                      <CardContent className="space-y-4 sm:space-y-6 px-0 pb-0">
                        {visibleSettings.map((setting, index) => {
                          // Check for nested settings
                          const childSettings = category.settings.filter(
                            s => s.depends_on?.key === setting.key && isSettingVisible(s)
                          );
                          const hasChildren = childSettings.length > 0;

                          return (
                            <div key={setting.key}>
                              {index > 0 && <Separator className="my-3 sm:my-4" />}
                              <SettingRenderer
                                setting={setting}
                                value={values[setting.key]}
                                saving={saving}
                                onChange={handleValueChange}
                              />

                              {/* Nested child settings */}
                              {hasChildren && (
                                <div className="mt-3 sm:mt-4 ml-4 sm:ml-8 pl-3 sm:pl-5 border-l-2 border-primary/20 space-y-3 sm:space-y-4">
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
            </div>
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
              onClick={() => {
                setResetDialogOpen(false);
                void resetToDefaults();
              }}
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
              onClick={() => {
                if (!resetSectionDialogOpen) return;
                const sectionKey = resetSectionDialogOpen;
                setResetSectionDialogOpen(null);
                void resetSection(sectionKey);
              }}
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
