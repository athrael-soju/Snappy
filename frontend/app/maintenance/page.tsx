"use client";

import "@/lib/api/client";

import { useRef } from "react";
import { useSearchParams } from "next/navigation";
import { Settings, Wrench, RefreshCw, Zap, Shield, Activity } from "lucide-react";
import { motion } from "framer-motion";

import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
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
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

const fadeIn = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.4 },
};

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
    <div className="flex min-h-screen flex-col bg-gradient-to-b from-muted/30 to-background">
      {/* Hero Header */}
      <div className="relative overflow-hidden border-b bg-gradient-to-br from-orange-500/10 via-orange-500/5 to-transparent">
        <div className="absolute inset-0 bg-grid-pattern opacity-30" />
        <div className="relative mx-auto max-w-7xl px-6 py-16 sm:px-8 lg:px-12">
          <motion.div {...fadeIn} className="space-y-6">
            <div className="flex items-start justify-between">
              <div className="space-y-4">
                <div className="flex items-center gap-3">
                  <div className="flex h-16 w-16 items-center justify-center rounded-3xl bg-gradient-to-br from-orange-500 to-orange-600 shadow-lg shadow-orange-500/25">
                    <Settings className="h-8 w-8 text-white" />
                  </div>
                  <div>
                    <h1 className="text-4xl font-bold tracking-tight text-foreground sm:text-5xl">
                      System Control
                    </h1>
                    <p className="mt-2 text-lg text-muted-foreground">
                      Configure runtime settings and manage your Snappy instance
                    </p>
                  </div>
                </div>
                
                {/* Quick Stats */}
                <div className="flex flex-wrap gap-4">
                  <div className="flex items-center gap-2 rounded-full bg-background/60 backdrop-blur-sm px-4 py-2 border">
                    <Activity className={`h-4 w-4 ${isSystemReady ? 'text-green-500' : 'text-orange-500'}`} />
                    <span className="text-sm font-medium">
                      {isSystemReady ? 'System Ready' : 'Not Initialized'}
                    </span>
                  </div>
                  <div className="flex items-center gap-2 rounded-full bg-background/60 backdrop-blur-sm px-4 py-2 border">
                    <Shield className="h-4 w-4 text-blue-500" />
                    <span className="text-sm font-medium">
                      {systemStatus?.collection?.vector_count ?? 0} Vectors
                    </span>
                  </div>
                  <div className="flex items-center gap-2 rounded-full bg-background/60 backdrop-blur-sm px-4 py-2 border">
                    <Zap className="h-4 w-4 text-purple-500" />
                    <span className="text-sm font-medium">
                      {systemStatus?.collection?.unique_files ?? 0} Documents
                    </span>
                  </div>
                </div>
              </div>

              {!isConfigurationView && (
                <Button onClick={fetchStatus} disabled={statusLoading} size="lg" className="gap-2">
                  <RefreshCw className={`h-4 w-4 ${statusLoading ? 'animate-spin' : ''}`} />
                  Refresh
                </Button>
              )}
            </div>
          </motion.div>
        </div>
      </div>

      {/* Main Content */}
      <div className="mx-auto w-full max-w-7xl flex-1 px-6 py-10 sm:px-8 lg:px-12">
        <Tabs defaultValue={section} className="space-y-8">
          <TabsList className="grid w-full max-w-md grid-cols-2 h-12">
            <TabsTrigger value="configuration" className="gap-2">
              <Settings className="h-4 w-4" />
              Configuration
            </TabsTrigger>
            <TabsTrigger value="data" className="gap-2">
              <Wrench className="h-4 w-4" />
              Maintenance
            </TabsTrigger>
          </TabsList>

          <TabsContent value="configuration" className="space-y-6">
            <Card className="border-2">
              <CardHeader className="border-b bg-muted/30">
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle>Runtime Configuration</CardTitle>
                    <CardDescription>
                      Adjust settings without restarting the backend. Changes take effect immediately.
                    </CardDescription>
                  </div>
                  <Badge variant="secondary" className="gap-1">
                    <Zap className="h-3 w-3" />
                    Live Config
                  </Badge>
                </div>
              </CardHeader>
              <CardContent className="p-6">
                <ConfigurationPanel ref={configPanelRef} />
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="data" className="space-y-6">
            {/* System Status Overview */}
            <div className="grid gap-4 lg:grid-cols-2">
              <CollectionStatusCard status={systemStatus?.collection ?? null} isLoading={statusLoading} />
              {!bucketDisabled && (
                <BucketStatusCard status={systemStatus?.bucket ?? null} isLoading={statusLoading} />
              )}
            </div>

            {/* Action Cards */}
            <Card className="border-2">
              <CardHeader className="border-b bg-muted/30">
                <CardTitle>System Actions</CardTitle>
                <CardDescription>
                  Manage your Snappy instance with these administrative operations.
                </CardDescription>
              </CardHeader>
              <CardContent className="p-6">
                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
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
              </CardContent>
            </Card>

            {/* Help Card */}
            <Card className="border-blue-200 dark:border-blue-900 bg-blue-50/50 dark:bg-blue-950/20">
              <CardContent className="flex items-start gap-4 p-6">
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-blue-500/10">
                  <Activity className="h-5 w-5 text-blue-600 dark:text-blue-400" />
                </div>
                <div className="space-y-2">
                  <h3 className="font-semibold text-foreground">System Health Tips</h3>
                  <ul className="space-y-1 text-sm text-muted-foreground">
                    <li>• Initialize Snappy after starting Qdrant and MinIO services</li>
                    <li>• Refresh status regularly to monitor collection and bucket statistics</li>
                    <li>• Use Data Reset carefully - it removes all stored documents and embeddings</li>
                    <li>• Delete system operations affect both vector database and object storage</li>
                  </ul>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
