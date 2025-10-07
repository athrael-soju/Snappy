"use client";

import "@/lib/api/client";
import { useRef } from "react";
import { useSearchParams } from "next/navigation";
import { Settings, RotateCcw } from "lucide-react";
import { motion } from "framer-motion";
import { defaultPageMotion, sectionVariants } from "@/lib/motion-presets";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Button } from "@/components/ui/button";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { ConfigurationPanel } from "@/components/configuration-panel";
import type { ConfigurationPanelHandle } from "@/components/configuration-panel";
import { PageHeader } from "@/components/page-header";
import { useSystemStatus, useMaintenanceActions, useSystemManagement } from "@/lib/hooks";
import {
  SystemStatusBadge,
  CollectionStatusCard,
  BucketStatusCard,
  InitializeCard,
  DeleteCard,
  DataResetCard,
} from "@/components/maintenance";
import { MAINTENANCE_ACTIONS } from "@/components/maintenance/constants";

export default function MaintenancePage() {
  const searchParams = useSearchParams();
  const section = searchParams.get("section") === "data" ? "data" : "configuration";

  const configPanelRef = useRef<ConfigurationPanelHandle>(null);

  const { systemStatus, statusLoading, fetchStatus, isSystemReady } = useSystemStatus();
  const { loading, dialogOpen, setDialogOpen, runAction } = useMaintenanceActions({
    onSuccess: fetchStatus,
  });
  const {
    initLoading,
    deleteLoading,
    deleteDialogOpen,
    setDeleteDialogOpen,
    handleInitialize,
    handleDelete,
  } = useSystemManagement({
    onSuccess: fetchStatus,
  });

  const criticalActions = MAINTENANCE_ACTIONS.filter(a => a.severity === "critical");
  const isConfigurationView = section !== "data";

  return (
    <motion.div {...defaultPageMotion} className="page-shell page-section flex min-h-0 flex-1 flex-col gap-10">
      <motion.section variants={sectionVariants}>
        <PageHeader
          title="System Maintenance"
          description={isConfigurationView ? "Manage runtime configuration options" : "Monitor and manage storage and indexing resources"}
          icon={Settings}
        />
      </motion.section>

      <motion.section variants={sectionVariants} className="flex-1 min-h-0 flex flex-col gap-8 pb-10">
        <div className="flex flex-wrap items-center justify-between gap-3 sm:gap-4">
          {!isConfigurationView && systemStatus && (
            <SystemStatusBadge
              isReady={isSystemReady}
              isLoading={statusLoading}
              onRefresh={fetchStatus}
            />
          )}
          {isConfigurationView && (
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => configPanelRef.current?.openResetDialog()}
                  className="h-10"
                >
                  <RotateCcw />
                </Button>
              </TooltipTrigger>
              <TooltipContent sideOffset={8}>
                <p>Reset configuration values</p>
              </TooltipContent>
            </Tooltip>
          )}
        </div>

        {isConfigurationView ? (
          <div className="flex-1 min-h-0">
            <ConfigurationPanel ref={configPanelRef} />
          </div>
        ) : (
          <ScrollArea className="custom-scrollbar flex-1 min-h-0">
            <div className="flex flex-col gap-6 pb-10 pr-2">
              <div className="flex flex-col gap-4">
                <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
                  <CollectionStatusCard
                    status={systemStatus?.collection || null}
                    isLoading={statusLoading}
                  />
                  <BucketStatusCard
                    status={systemStatus?.bucket || null}
                    isLoading={statusLoading}
                  />
                </div>

                <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
                  <InitializeCard
                    isLoading={initLoading}
                    isSystemReady={isSystemReady}
                    isDeleteLoading={deleteLoading}
                    onInitialize={handleInitialize}
                  />

                  <DeleteCard
                    isLoading={deleteLoading}
                    isInitLoading={initLoading}
                    isSystemReady={isSystemReady}
                    dialogOpen={deleteDialogOpen}
                    onDialogChange={setDeleteDialogOpen}
                    onDelete={handleDelete}
                  />

                  {criticalActions.map((action) => (
                    <DataResetCard
                      key={action.id}
                      action={action}
                      isLoading={loading[action.id]}
                      isInitLoading={initLoading}
                      isDeleteLoading={deleteLoading}
                      isSystemReady={isSystemReady}
                      dialogOpen={dialogOpen === action.id}
                      onDialogChange={(open) => setDialogOpen(open ? action.id : null)}
                      onConfirm={runAction}
                    />
                  ))}
                </div>
              </div>
            </div>
          </ScrollArea>
        )}
      </motion.section>
    </motion.div>
  );
}


