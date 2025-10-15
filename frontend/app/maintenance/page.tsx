"use client";

import "@/lib/api/client";
import { useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { AppPage } from "@/components/layout";
import { cn } from "@/lib/utils";
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
  const router = useRouter();
  const searchParams = useSearchParams();
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
  const bucketDisabled = systemStatus?.bucket?.disabled === true;
  const section = searchParams.get("section");

  useEffect(() => {
    if (!section) return;

    if (section === "configuration") {
      router.replace("/configuration");
      return;
    }

    if (section !== "data") {
      router.replace("/maintenance");
    }
  }, [router, section]);

  return (
    <AppPage
      title="Maintenance"
      description="Monitor storage health, manage indexes, and perform administrative actions."
      actions={(
        <Button
          variant="outline"
          size="sm"
          onClick={() => {
            void fetchStatus();
          }}
          disabled={statusLoading}
        >
          Refresh status
        </Button>
      )}
    >
      <div className="stack stack-lg">
        <div
          className={cn("grid gap-5", {
            "lg:grid-cols-2": !bucketDisabled,
          })}
        >
          <CollectionStatusCard
            status={systemStatus?.collection || null}
            isLoading={statusLoading}
          />
          {!bucketDisabled ? (
            <BucketStatusCard
              status={systemStatus?.bucket || null}
              isLoading={statusLoading}
            />
          ) : null}
        </div>

        <div className="grid gap-5 lg:grid-cols-3">
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
    </AppPage>
  );
}
