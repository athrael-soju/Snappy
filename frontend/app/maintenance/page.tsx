"use client";

import "@/lib/api/client";
import { useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Database } from "lucide-react";
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
    <PageLayout
      title="System Maintenance"
      icon={Database}
      tooltip="Monitor and manage storage and indexing resources"
      className="flex flex-col gap-4"
    >
      <div className="flex-shrink-0 flex flex-col gap-3 sm:gap-4">
        <SystemStatusBadge
          isReady={isSystemReady}
          isLoading={statusLoading}
          onRefresh={fetchStatus}
        />
      </div>
      
      <div className="flex-1 min-h-0">
        <div 
          className="h-full overflow-y-auto rounded-2xl bg-white/70 p-4 shadow"
          style={{ overscrollBehavior: 'contain', scrollbarGutter: 'stable' }}
        >
          <div className="flex w-full flex-col gap-4 sm:gap-6">
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
          </div>
        </div>
    </PageLayout>
  );
}


