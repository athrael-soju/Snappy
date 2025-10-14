"use client";

import "@/lib/api/client";
import { useRef } from "react";
import { useSearchParams } from "next/navigation";
import { Settings, Database } from "lucide-react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { ConfigurationPanel } from "@/components/configuration-panel";
import type { ConfigurationPanelHandle } from "@/components/configuration-panel";
import { PageLayout } from "@/components/layout/page-layout";
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
  const bucketDisabled = systemStatus?.bucket?.disabled === true;

  return (
    <PageLayout
      title={isConfigurationView ? "System Configuration" : "System Maintenance"}
      icon={isConfigurationView ? Settings : Database}
      tooltip={isConfigurationView ? "Manage runtime configuration options" : "Monitor and manage storage and indexing resources"}
      className="h-full"
    >
      {isConfigurationView ? (
        <ConfigurationPanel ref={configPanelRef} />
      ) : (
        <div className="flex-1 min-h-0">
          <ScrollArea className="h-full">
            <div className="flex w-full flex-col gap-4 sm:gap-6 px-3 sm:px-4 pb-6 sm:pb-8">
              <div className={`grid grid-cols-1 gap-4 sm:gap-5 ${bucketDisabled ? "" : "lg:grid-cols-2"}`}>
                  <CollectionStatusCard
                    status={systemStatus?.collection || null}
                    isLoading={statusLoading}
                  />
                  {!bucketDisabled && (
                    <BucketStatusCard
                      status={systemStatus?.bucket || null}
                      isLoading={statusLoading}
                    />
                  )}
              </div>

              <div className="grid grid-cols-1 gap-4 sm:gap-5 lg:grid-cols-3">
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
        </div>
      )}
    </PageLayout>
  );
}


