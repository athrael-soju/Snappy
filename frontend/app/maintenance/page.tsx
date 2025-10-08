"use client";
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
    <motion.div {...defaultPageMotion}>
      <motion.section variants={sectionVariants} className="flex flex-col items-center text-center gap-6 pt-6 sm:pt-8">
        <PageHeader
          title={isConfigurationView ? "System Configuration" : "System Maintenance"}
          tooltip={isConfigurationView ? "Manage runtime configuration options" : "Monitor and manage storage and indexing resources"}
        />
      </motion.section>

      <motion.section variants={sectionVariants} className="flex-1 min-h-0 flex flex-col gap-6 pb-6 sm:pb-8 pt-8">
        {isConfigurationView ? (
          <div className="mx-auto flex w-full max-w-6xl flex-1 min-h-0 flex-col">
            <ConfigurationPanel ref={configPanelRef} />
          </div>
        ) : (
          <div className="mx-auto flex w-full max-w-6xl flex-1 min-h-0 gap-6">
            <ScrollArea className="h-[calc(100vh-15rem)]">
              <div className="flex w-full flex-col gap-6 p-4 pb-8">
                <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
                  <CollectionStatusCard
                    status={systemStatus?.collection || null}
                    isLoading={statusLoading}
                  />
                  <BucketStatusCard
                    status={systemStatus?.bucket || null}
                    isLoading={statusLoading}
                  />
                </div>

                <div className="grid grid-cols-1 gap-5 lg:grid-cols-3">
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
            </ScrollArea>

            {/* System Status Badge - Right Side */}
            {/* {systemStatus && (
              <div className="flex flex-col justify-start pt-4 w-52 flex-shrink-0">
                <SystemStatusBadge
                  isReady={isSystemReady}
                  isLoading={statusLoading}
                  onRefresh={fetchStatus}
                />
              </div>
            )} */}
          </div>
        )}
      </motion.section>
    </motion.div>
  );
}


