"use client";

import "@/lib/api/client";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Settings, Shield, Sliders } from "lucide-react";
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
  // Custom hooks for business logic
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

  const criticalActions = MAINTENANCE_ACTIONS.filter(a => a.severity === 'critical');

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="flex flex-col min-h-0 flex-1"
    >
      <PageHeader
        title="System Maintenance"
        description="Manage your vector database, object storage, and runtime configuration"
        icon={Settings}
      />

      <Tabs defaultValue="configuration" className="flex-1 flex flex-col min-h-0">
        <div className="flex items-center justify-between mb-4 gap-4">
          <TabsList className="flex-1 max-w-md mx-auto bg-gradient-to-r from-blue-100/50 via-purple-100/50 to-cyan-100/50 border border-blue-200/50 h-14 rounded-full p-1 shadow-sm">
            <TabsTrigger
              value="configuration"
              className="flex-1 data-[state=active]:bg-gradient-to-r data-[state=active]:from-blue-600 data-[state=active]:to-purple-600 data-[state=active]:text-white data-[state=active]:shadow-lg transition-all duration-300 rounded-full font-medium"
            >
              <Sliders className="w-4 h-4 mr-2" />
              <span className="hidden sm:inline">Configuration</span>
              <span className="sm:hidden">Config</span>
            </TabsTrigger>          
            <TabsTrigger
              value="data_management"
              className="flex-1 data-[state=active]:bg-gradient-to-r data-[state=active]:from-blue-600 data-[state=active]:to-purple-600 data-[state=active]:text-white data-[state=active]:shadow-lg transition-all duration-300 rounded-full font-medium"
            >
              <Shield className="w-4 h-4 mr-2" />
              <span className="hidden sm:inline">Data Management</span>
              <span className="sm:hidden">Data</span>
            </TabsTrigger>
          </TabsList>
          
          {systemStatus && (
            <SystemStatusBadge
              isReady={isSystemReady}
              isLoading={statusLoading}
              onRefresh={fetchStatus}
            />
          )}
        </div>

        {/* Configuration Tab */}
        <TabsContent value="configuration" className="flex-1 min-h-0 mt-0 h-full">
          <div className="h-full flex flex-col">
            <ConfigurationPanel />
          </div>
        </TabsContent>

        {/* Data Management Tab */}
        <TabsContent value="data_management" className="flex-1 min-h-0 overflow-y-auto mt-0 custom-scrollbar pr-2">
          <div className="space-y-6 pb-4">
            {/* System Status */}
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

              {/* Management Actions */}
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
        </TabsContent>
      </Tabs>
    </motion.div>
  );
}
