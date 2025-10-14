"use client";

import "@/lib/api/client";

import { useRef } from "react";
import { useSearchParams } from "next/navigation";
import { Settings, Wrench } from "lucide-react";

import { PageHeader } from "@/components/page-header";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Button } from "@/components/ui/button";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { ConfigurationPanel } from "@/components/configuration-panel";
import type { ConfigurationPanelHandle } from "@/components/configuration-panel";
import { useSystemStatus, useMaintenanceActions, useSystemManagement } from "@/lib/hooks";
import {
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
  const isConfigurationView = section !== "data";

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

  const criticalActions = MAINTENANCE_ACTIONS.filter((action) => action.severity === "critical");
  const bucketDisabled = systemStatus?.bucket?.disabled === true;

  return (
    <div className="mx-auto flex w-full max-w-6xl flex-1 flex-col gap-6 px-4 py-8 sm:px-6 lg:px-8">
      <PageHeader
        title={isConfigurationView ? "System configuration" : "System maintenance"}
        description={
          isConfigurationView
            ? "Update runtime settings for Snappy without restarting the backend."
            : "Monitor storage, initialise services, and reset data when needed."
        }
        icon={isConfigurationView ? Settings : Wrench}
      >
        {!isConfigurationView && (
          <Tooltip>
            <TooltipTrigger asChild>
              <Button size="sm" variant="outline" onClick={fetchStatus} disabled={statusLoading}>
                Refresh status
              </Button>
            </TooltipTrigger>
            <TooltipContent>Fetch the latest service stats</TooltipContent>
          </Tooltip>
        )}
      </PageHeader>

      {isConfigurationView ? (
        <div className="rounded-xl border bg-card p-4 sm:p-6">
          <ConfigurationPanel ref={configPanelRef} />
        </div>
      ) : (
        <div className="grid gap-6 lg:grid-cols-[2fr_1fr]">
          <ScrollArea className="h-[calc(100vh-18rem)] rounded-xl border bg-card p-4">
            <div className="flex flex-col gap-6">
              <div className={`grid gap-4 ${bucketDisabled ? "grid-cols-1" : "grid-cols-1 lg:grid-cols-2"}`}>
                <CollectionStatusCard status={systemStatus?.collection ?? null} isLoading={statusLoading} />
                {!bucketDisabled && (
                  <BucketStatusCard status={systemStatus?.bucket ?? null} isLoading={statusLoading} />
                )}
              </div>

              <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
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

          <div className="space-y-4 rounded-xl border bg-card p-4">
            <h2 className="text-sm font-semibold text-foreground">Service status</h2>
            <p className="text-sm text-muted-foreground">
              Refresh to confirm the latest collection and bucket statistics. Initialise Snappy after you start Qdrant
              and MinIO.
            </p>
            <Button onClick={fetchStatus} disabled={statusLoading} size="sm" className="w-full">
              {statusLoading ? "Refreshing…" : "Refresh now"}
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
