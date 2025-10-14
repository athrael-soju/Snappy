"use client";

import { useState, forwardRef, useImperativeHandle } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ButtonGroup } from "@/components/ui/button-group";
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

      {/* Main content - with proper height constraints */}
      <div className="flex-1 min-h-0 flex gap-6 pr-4">
        {/* Left rail navigation */}
        <ConfigurationTabs
          categories={categoriesToRender}
          activeTab={activeCategoryKey}
          onTabChange={setActiveTab}
        />

        {/* Main content area */}
        <div className="flex-1 min-w-0 flex flex-col gap-6">
          {/* Action Button Group */}
          <Card className="overflow-hidden">
            <CardContent className="p-0">
              <ButtonGroup className="shadow-sm !w-full [&>*]:flex-1 [&>*]:h-12">
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={optimizeForSystem}
                    disabled={saving || optimizing}
                    className="gap-2 px-4 border-0 text-purple-600 dark:text-purple-400 hover:text-purple-700 dark:hover:text-purple-300 !rounded-none"
                  >
                    {optimizing ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        Optimizing...
                      </>
                    ) : (
                      <>
                        <Sparkles className="w-4 h-4" />
                        Optimize
                      </>
                    )}
                  </Button>
                </TooltipTrigger>
                <TooltipContent sideOffset={8} className="bg-popover text-popover-foreground border-border">
                  <p>Detect this server&apos;s hardware and apply recommended settings</p>
                </TooltipContent>
              </Tooltip>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setResetSectionDialogOpen(activeCategoryKey)}
                    disabled={saving}
                    className="gap-2 px-4 border-0 !rounded-none"
                  >
                    <RotateCcw className="w-4 h-4" />
                    Reset Section
                  </Button>
                </TooltipTrigger>
                <TooltipContent sideOffset={8} className="bg-popover text-popover-foreground border-border">
                  <p>Reset current section to defaults</p>
                </TooltipContent>
              </Tooltip>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setResetDialogOpen(true)}
                    disabled={saving}
                    className="gap-2 px-4 border-0 text-destructive hover:text-destructive/90 !rounded-none"
                  >
                    <RotateCcw className="w-4 h-4" />
                    Reset All
                  </Button>
                </TooltipTrigger>
                <TooltipContent sideOffset={8} className="bg-popover text-popover-foreground border-border">
                  <p>Reset all configuration to defaults</p>
                </TooltipContent>
              </Tooltip>
            </ButtonGroup>
            </CardContent>
          </Card>

          <ScrollArea className="h-[calc(100vh-20rem)]">
            <div className="px-1 py-2 pr-4">
              {categoriesToRender.map(([categoryKey, category]) => {
                if (activeCategoryKey !== categoryKey) return null;

                // Filter to show only top-level settings (exclude nested children with depends_on)
                const visibleSettings = category.settings.filter(s => isSettingVisible(s) && !s.depends_on);

                return (
                  <motion.div
                    key={categoryKey}
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: -20 }}
                    transition={{ duration: 0.2 }}
                    className="flex-1 min-h-0"
                  >
                    {/* Settings Card - Scrollable */}
                    <Card className="flex flex-1 min-h-0 flex-col overflow-hidden">
                      <CardHeader className="flex-shrink-0 px-6 pt-6">
                        <div className="flex items-start gap-3">
                          <div className="flex size-12 items-center justify-center rounded-xl bg-primary/10 text-primary">
                            <Settings className="w-6 h-6" />
                          </div>
                          <div>
                            <CardTitle className="text-xl font-semibold text-foreground">{category.name}</CardTitle>
                            <CardDescription className="mt-1 text-base leading-relaxed text-muted-foreground">{category.description}</CardDescription>
                          </div>
                        </div>
                      </CardHeader>

                      <CardContent className="flex-1 min-h-0 overflow-y-auto space-y-6 px-6 pb-6">
                        {visibleSettings.map((setting, index) => {
                          // Check for nested settings
                          const childSettings = category.settings.filter(
                            s => s.depends_on?.key === setting.key && isSettingVisible(s)
                          );
                          const hasChildren = childSettings.length > 0;

                          return (
                            <div key={setting.key}>
                              {index > 0 && <Separator className="my-3" />}
                              <SettingRenderer
                                setting={setting}
                                value={values[setting.key]}
                                saving={saving}
                                onChange={handleValueChange}
                              />

                              {/* Nested child settings */}
                              {hasChildren && (
                                <div className="mt-4 ml-6 space-y-4 border-l border-muted pl-4">
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

                    </Card>

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
