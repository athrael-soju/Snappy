"use client";

import "@/lib/api/client";
import { useSearchParams } from "next/navigation";
import { Settings } from "lucide-react";
import { motion } from "framer-motion";
import { ConfigurationPanel } from "@/components/configuration-panel";
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
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="page-shell page-section flex flex-col min-h-0 flex-1"
    >
      <PageHeader
        title="System Maintenance"
        description={isConfigurationView ? "Manage runtime configuration options" : "Monitor and manage storage and indexing resources"}
        icon={Settings}
      />

      <div className="flex-1 min-h-0 flex flex-col space-y-8 pb-6">
        <div className="flex items-center justify-end flex-shrink-0">
          {systemStatus && (
            <SystemStatusBadge
              isReady={isSystemReady}
              isLoading={statusLoading}
              onRefresh={fetchStatus}
            />
          )}
        </div>

        {isConfigurationView ? (
          <div className="flex-1 min-h-0 overflow-y-auto custom-scrollbar pr-2">
            <div className="space-y-6 pb-4">
              <ConfigurationPanel />
            </div>
          </div>
        ) : (
          <div className="flex-1 min-h-0 overflow-y-auto custom-scrollbar pr-2">
            <div className="space-y-6 pb-4">
              <div className="space-y-4">
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                  <CollectionStatusCard
                    status={systemStatus?.collection || null}
                    isLoading={statusLoading}
                  />
                  <BucketStatusCard
                    status={systemStatus?.bucket || null}
                    isLoading={statusLoading}
                  />
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
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
        )}
      </div>
    </motion.div>
  );
}
