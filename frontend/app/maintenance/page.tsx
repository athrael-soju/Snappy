"use client";

import { useState, useEffect } from "react";
import { MaintenanceService, ApiError } from "@/lib/api/generated";
import "@/lib/api/client";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Settings, Database, Server, Trash2, AlertTriangle, Loader2, Shield, Sliders, CheckCircle2, XCircle, PlayCircle, RefreshCw } from "lucide-react";
import { motion } from "framer-motion";
import { toast } from "@/components/ui/sonner";
import { ConfigurationPanel } from "@/components/configuration-panel";
import { PageHeader } from "@/components/page-header";

type ActionType = "q" | "m" | "all";

interface CollectionStatus {
  name: string;
  exists: boolean;
  vector_count: number;
  unique_files: number;
  error: string | null;
}

interface BucketStatus {
  name: string;
  exists: boolean;
  object_count: number;
  error: string | null;
}

interface SystemStatus {
  collection: CollectionStatus;
  bucket: BucketStatus;
}

const actions = [
  {
    id: "all" as ActionType,
    title: "Data Reset",
    description: "Removes all data from both systems",
    detailedDescription: "This will delete all documents, embeddings, images, and search indices. The system will return to its initial empty state.",
    icon: Trash2,
    color: "text-red-600",
    bgColor: "bg-red-500/10",
    borderColor: "border-red-300",
    buttonVariant: "destructive" as const,
    confirmTitle: "Data Reset?",
    confirmMsg: "⚠️ DANGER: This will permanently delete ALL data from both Qdrant and MinIO. This includes all documents, embeddings, images, and search indices. This action cannot be undone and will reset the entire system to its initial state.",
    successMsg: "System completely reset",
    severity: "critical" as const
  }
];

export default function MaintenancePage() {
  const [loading, setLoading] = useState<{ q: boolean; m: boolean; all: boolean }>({ q: false, m: false, all: false });
  const [dialogOpen, setDialogOpen] = useState<ActionType | null>(null);
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);
  const [statusLoading, setStatusLoading] = useState(false);
  const [initLoading, setInitLoading] = useState(false);
  const [deleteLoading, setDeleteLoading] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  // No system health state stored locally; rely directly on localStorage when needed

  async function run(action: ActionType) {
    const actionConfig = actions.find(a => a.id === action);
    if (!actionConfig) return;

    setLoading((s) => ({ ...s, [action]: true }));
    setDialogOpen(null);

    try {
      let res: any;
      if (action === "q") res = await MaintenanceService.clearQdrantClearQdrantPost();
      else if (action === "m") res = await MaintenanceService.clearMinioClearMinioPost();
      else res = await MaintenanceService.clearAllClearAllPost();

      const msg = typeof res === "object" && res !== null
        ? (res.message ?? JSON.stringify(res))
        : String(res ?? "Operation completed successfully");

      toast.success(actionConfig.successMsg, { description: msg });

      // Update stats
      const prevTotal = parseInt(localStorage.getItem("maintenance_operations") || "0");
      const newTotal = prevTotal + 1;
      localStorage.setItem("maintenance_operations", newTotal.toString());
      localStorage.setItem("last_maintenance_action", new Date().toISOString());
    } catch (err: unknown) {
      let errorMsg = "Maintenance action failed";
      if (err instanceof ApiError) {
        errorMsg = `${err.status}: ${err.message}`;
      } else if (err instanceof Error) {
        errorMsg = err.message;
      }
      toast.error("Action failed", { description: errorMsg });
    } finally {
      setLoading((s) => ({ ...s, [action]: false }));
    }
  }

  async function fetchStatus() {
    setStatusLoading(true);
    try {
      const status = await MaintenanceService.getStatusStatusGet();
      setSystemStatus(status as SystemStatus);
    } catch (err: unknown) {
      let errorMsg = "Failed to fetch status";
      if (err instanceof ApiError) {
        errorMsg = `${err.status}: ${err.message}`;
      } else if (err instanceof Error) {
        errorMsg = err.message;
      }
      toast.error("Status Check Failed", { description: errorMsg });
    } finally {
      setStatusLoading(false);
    }
  }

  async function handleInitialize() {
    setInitLoading(true);
    try {
      const result = await MaintenanceService.initializeInitializePost();
      
      if (result.status === "success") {
        toast.success("Initialization Complete", { 
          description: "Collection and bucket are ready to use" 
        });
      } else if (result.status === "partial") {
        toast.warning("Partial Initialization", { 
          description: "Some components failed to initialize. Check details." 
        });
      } else {
        toast.error("Initialization Failed", { 
          description: "Failed to initialize collection and bucket" 
        });
      }
      
      // Refresh status and clear cache to force refresh on other pages
      await fetchStatus();
      // Dispatch event to notify other pages
      window.dispatchEvent(new CustomEvent('systemStatusChanged'));
    } catch (err: unknown) {
      let errorMsg = "Initialization failed";
      if (err instanceof ApiError) {
        errorMsg = `${err.status}: ${err.message}`;
      } else if (err instanceof Error) {
        errorMsg = err.message;
      }
      toast.error("Initialization Failed", { description: errorMsg });
    } finally {
      setInitLoading(false);
    }
  }

  async function handleDelete() {
    setDeleteLoading(true);
    setDeleteDialogOpen(false);
    try {
      const result = await MaintenanceService.deleteCollectionAndBucketDeleteDelete();
      
      if (result.status === "success") {
        toast.success("Deletion Complete", { 
          description: "Collection and bucket have been deleted" 
        });
      } else if (result.status === "partial") {
        toast.warning("Partial Deletion", { 
          description: "Some components failed to delete. Check details." 
        });
      } else {
        toast.error("Deletion Failed", { 
          description: "Failed to delete collection and bucket" 
        });
      }
      
      // Refresh status and clear cache to force refresh on other pages
      await fetchStatus();
      // Dispatch event to notify other pages
      window.dispatchEvent(new CustomEvent('systemStatusChanged'));
    } catch (err: unknown) {
      let errorMsg = "Deletion failed";
      if (err instanceof ApiError) {
        errorMsg = `${err.status}: ${err.message}`;
      } else if (err instanceof Error) {
        errorMsg = err.message;
      }
      toast.error("Deletion Failed", { description: errorMsg });
    } finally {
      setDeleteLoading(false);
    }
  }

  // Fetch status on mount and when tab changes to data_management
  useEffect(() => {
    fetchStatus();
  }, []);

  const isAnyLoading = loading.q || loading.m || loading.all;
  const isSystemReady = systemStatus?.collection.exists && systemStatus?.bucket.exists;

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

      {/* Tabs Container with Scroll */}
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
          
          {/* System Status Badge */}
          {systemStatus && (
            <div className="flex items-center gap-2">
              <Badge 
                variant={isSystemReady ? "default" : "secondary"}
                className={`h-10 px-4 ${isSystemReady ? 'bg-green-600 hover:bg-green-700' : 'bg-amber-500 hover:bg-amber-600'} text-white`}
              >
                {isSystemReady ? (
                  <><CheckCircle2 className="w-4 h-4 mr-2" /> Ready</>
                ) : (
                  <><AlertTriangle className="w-4 h-4 mr-2" /> Not Initialized</>
                )}
              </Badge>
              <Button
                variant="outline"
                size="sm"
                onClick={fetchStatus}
                disabled={statusLoading}
                className="h-10"
              >
                {statusLoading ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <RefreshCw className="w-4 h-4" />
                )}
              </Button>
            </div>
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
            {/* System Status and Management */}
            <div className="space-y-4">
              {/* Collection and Bucket Status */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                {/* Qdrant Collection Status */}
                <Card className="border border-blue-200/50 bg-gradient-to-br from-blue-500/5 to-cyan-500/5">
                  <CardHeader className="pb-3">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-3">
                        <div className="p-2 rounded-xl bg-blue-100 border-2 border-blue-200/50">
                          <Database className="w-5 h-5 text-blue-600" />
                        </div>
                        <div>
                          <CardTitle className="text-base font-semibold">Qdrant Collection</CardTitle>
                          <CardDescription className="text-xs">Vector Database</CardDescription>
                        </div>
                      </div>
                      {systemStatus && (
                        systemStatus.collection.exists ? (
                          <Badge className="bg-green-100 text-green-700 border-green-300">
                            <CheckCircle2 className="w-3 h-3 mr-1" />
                            Active
                          </Badge>
                        ) : (
                          <Badge variant="secondary" className="bg-gray-100 text-gray-700">
                            <XCircle className="w-3 h-3 mr-1" />
                            Not Found
                          </Badge>
                        )
                      )}
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    {statusLoading ? (
                      <div className="flex items-center justify-center py-8">
                        <Loader2 className="w-6 h-6 animate-spin text-blue-500" />
                      </div>
                    ) : systemStatus ? (
                      <>
                        <div className="space-y-2 text-sm">
                          <div className="flex justify-between items-center p-2 bg-blue-50/50 rounded">
                            <span className="text-muted-foreground">Collection Name:</span>
                            <span className="font-medium">{systemStatus.collection.name}</span>
                          </div>
                          <div className="flex justify-between items-center p-2 bg-blue-50/50 rounded">
                            <span className="text-muted-foreground">Vector Count:</span>
                            <span className="font-medium">{systemStatus.collection.vector_count.toLocaleString()}</span>
                          </div>
                          <div className="flex justify-between items-center p-2 bg-blue-50/50 rounded">
                            <span className="text-muted-foreground">Unique Files:</span>
                            <span className="font-medium">{systemStatus.collection.unique_files.toLocaleString()}</span>
                          </div>
                        </div>
                        {systemStatus.collection.error && (
                          <div className="p-2 bg-red-50 border border-red-200 rounded text-xs text-red-700">
                            Error: {systemStatus.collection.error}
                          </div>
                        )}
                        <div className="mt-3 pt-3 border-t border-blue-200/30 space-y-2 text-xs">
                          <div className="flex items-start gap-2">
                            <div className="w-1.5 h-1.5 bg-blue-500 rounded-full mt-1 flex-shrink-0"></div>
                            <span className="text-muted-foreground">Document embeddings and vector representations</span>
                          </div>
                          <div className="flex items-start gap-2">
                            <div className="w-1.5 h-1.5 bg-blue-500 rounded-full mt-1 flex-shrink-0"></div>
                            <span className="text-muted-foreground">Search indices for visual content retrieval</span>
                          </div>
                          <div className="flex items-start gap-2">
                            <div className="w-1.5 h-1.5 bg-blue-500 rounded-full mt-1 flex-shrink-0"></div>
                            <span className="text-muted-foreground">AI-generated semantic understanding data</span>
                          </div>
                        </div>
                      </>
                    ) : (
                      <p className="text-sm text-muted-foreground">No status available</p>
                    )}
                  </CardContent>
                </Card>

                {/* MinIO Bucket Status */}
                <Card className="border border-orange-200/50 bg-gradient-to-br from-orange-500/5 to-amber-500/5">
                  <CardHeader className="pb-3">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-3">
                        <div className="p-2 rounded-xl bg-orange-100 border-2 border-orange-200/50">
                          <Server className="w-5 h-5 text-orange-600" />
                        </div>
                        <div>
                          <CardTitle className="text-base font-semibold">MinIO Bucket</CardTitle>
                          <CardDescription className="text-xs">Object Storage</CardDescription>
                        </div>
                      </div>
                      {systemStatus && (
                        systemStatus.bucket.exists ? (
                          <Badge className="bg-green-100 text-green-700 border-green-300">
                            <CheckCircle2 className="w-3 h-3 mr-1" />
                            Active
                          </Badge>
                        ) : (
                          <Badge variant="secondary" className="bg-gray-100 text-gray-700">
                            <XCircle className="w-3 h-3 mr-1" />
                            Not Found
                          </Badge>
                        )
                      )}
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    {statusLoading ? (
                      <div className="flex items-center justify-center py-8">
                        <Loader2 className="w-6 h-6 animate-spin text-orange-500" />
                      </div>
                    ) : systemStatus ? (
                      <>
                        <div className="space-y-2 text-sm">
                          <div className="flex justify-between items-center p-2 bg-orange-50/50 rounded">
                            <span className="text-muted-foreground">Bucket Name:</span>
                            <span className="font-medium">{systemStatus.bucket.name}</span>
                          </div>
                          <div className="flex justify-between items-center p-2 bg-orange-50/50 rounded">
                            <span className="text-muted-foreground">Object Count:</span>
                            <span className="font-medium">{systemStatus.bucket.object_count.toLocaleString()}</span>
                          </div>
                        </div>
                        {systemStatus.bucket.error && (
                          <div className="p-2 bg-red-50 border border-red-200 rounded text-xs text-red-700">
                            Error: {systemStatus.bucket.error}
                          </div>
                        )}
                        <div className="mt-3 pt-3 border-t border-orange-200/30 space-y-2 text-xs">
                          <div className="flex items-start gap-2">
                            <div className="w-1.5 h-1.5 bg-orange-500 rounded-full mt-1 flex-shrink-0"></div>
                            <span className="text-muted-foreground">Original uploaded documents and images</span>
                          </div>
                          <div className="flex items-start gap-2">
                            <div className="w-1.5 h-1.5 bg-orange-500 rounded-full mt-1 flex-shrink-0"></div>
                            <span className="text-muted-foreground">Processed file thumbnails and previews</span>
                          </div>
                          <div className="flex items-start gap-2">
                            <div className="w-1.5 h-1.5 bg-orange-500 rounded-full mt-1 flex-shrink-0"></div>
                            <span className="text-muted-foreground">File metadata and storage organization</span>
                          </div>
                        </div>
                      </>
                    ) : (
                      <p className="text-sm text-muted-foreground">No status available</p>
                    )}
                  </CardContent>
                </Card>
              </div>

              {/* Management Actions */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
                {/* Initialize Action */}
                <Card className="border-2 border-green-200/50 bg-gradient-to-br from-green-500/5 to-emerald-500/5">
                  <CardHeader className="pb-3">
                    <div className="flex items-center gap-3">
                      <div className="p-2 rounded-xl bg-green-100 border-2 border-green-200/50">
                        <PlayCircle className="w-5 h-5 text-green-600" />
                      </div>
                      <div>
                        <CardTitle className="text-base font-semibold text-green-900">Initialize System</CardTitle>
                        <CardDescription className="text-sm">Create collection and bucket</CardDescription>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-muted-foreground mb-4">
                      Creates the Qdrant collection and MinIO bucket based on your current configuration settings. Required before uploading files.
                    </p>
                    <Button
                      onClick={handleInitialize}
                      disabled={initLoading || deleteLoading || isSystemReady}
                      className="w-full bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 text-white"
                    >
                      {initLoading ? (
                        <>
                          <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                          Initializing...
                        </>
                      ) : (
                        <>
                          <PlayCircle className="w-4 h-4 mr-2" />
                          Initialize
                        </>
                      )}
                    </Button>
                  </CardContent>
                </Card>

                {/* Delete Action */}
                <Card className="border-2 border-red-200/50 bg-gradient-to-br from-red-500/5 to-pink-500/5">
                  <CardHeader className="pb-3">
                    <div className="flex items-center gap-3">
                      <div className="p-2 rounded-xl bg-red-100 border-2 border-red-200/50">
                        <Trash2 className="w-5 h-5 text-red-600" />
                      </div>
                      <div>
                        <CardTitle className="text-base font-semibold text-red-900">Delete System</CardTitle>
                        <CardDescription className="text-sm">Remove collection and bucket</CardDescription>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-muted-foreground mb-4">
                      Permanently deletes the Qdrant collection and MinIO bucket including all data. Use this to change configuration or start fresh.
                    </p>
                    <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
                      <DialogTrigger asChild>
                        <Button
                          variant="destructive"
                          disabled={deleteLoading || initLoading || !isSystemReady}
                          className="w-full"
                        >
                          {deleteLoading ? (
                            <>
                              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                              Deleting...
                            </>
                          ) : (
                            <>
                              <Trash2 className="w-4 h-4 mr-2" />
                              Delete
                            </>
                          )}
                        </Button>
                      </DialogTrigger>
                      <DialogContent>
                        <DialogHeader>
                          <DialogTitle className="flex items-center gap-2">
                            <Trash2 className="w-5 h-5 text-red-600" />
                            Delete Collection and Bucket?
                          </DialogTitle>
                          <DialogDescription className="pt-2">
                            This will permanently delete the Qdrant collection and MinIO bucket, including all vectors, files, and metadata. This action cannot be undone.
                          </DialogDescription>
                        </DialogHeader>
                        <div className="bg-red-50 p-4 rounded-lg border-l-4 border-red-400">
                          <div className="flex items-start gap-2">
                            <AlertTriangle className="w-4 h-4 text-red-600 mt-0.5 flex-shrink-0" />
                            <p className="text-sm text-red-800">
                              <strong>Warning:</strong> All uploaded documents, embeddings, and search indices will be permanently lost.
                            </p>
                          </div>
                        </div>
                        <DialogFooter>
                          <Button
                            variant="outline"
                            onClick={() => setDeleteDialogOpen(false)}
                          >
                            Cancel
                          </Button>
                          <Button
                            variant="destructive"
                            onClick={handleDelete}
                          >
                            <Trash2 className="w-4 h-4 mr-2" />
                            Confirm Delete
                          </Button>
                        </DialogFooter>
                      </DialogContent>
                    </Dialog>
                  </CardContent>
                </Card>

                {/* Data Reset Action */}
                {actions.filter(a => a.severity === 'critical').map((action) => {
                  const Icon = action.icon;
                  const isLoading = loading[action.id];

                  return (
                    <Card key={action.id} className="border-2 border-amber-200/50 bg-gradient-to-br from-amber-500/5 to-orange-500/5">
                      <CardHeader className="pb-3">
                        <div className="flex items-center gap-3">
                          <div className="p-2 rounded-xl bg-amber-100 border-2 border-amber-200/50">
                            <Icon className="w-5 h-5 text-amber-600" />
                          </div>
                          <div>
                            <CardTitle className="text-base font-semibold text-amber-900">{action.title}</CardTitle>
                            <CardDescription className="text-sm">{action.description}</CardDescription>
                          </div>
                        </div>
                      </CardHeader>
                      <CardContent>
                        <p className="text-sm text-muted-foreground mb-4">
                          {action.detailedDescription}
                        </p>
                        <Dialog open={dialogOpen === action.id} onOpenChange={(open) => setDialogOpen(open ? action.id : null)}>
                          <DialogTrigger asChild>
                            <Button
                              variant="destructive"
                              disabled={isAnyLoading}
                              className="w-full bg-gradient-to-r from-amber-600 to-orange-600 hover:from-amber-700 hover:to-orange-700"
                            >
                              {isLoading ? (
                                <>
                                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                                  Processing...
                                </>
                              ) : (
                                <>
                                  <Icon className="w-4 h-4 mr-2" />
                                  {action.title}
                                </>
                              )}
                            </Button>
                          </DialogTrigger>
                          <DialogContent className="max-w-md">
                            <DialogHeader>
                              <DialogTitle className="flex items-center gap-2 text-lg">
                                <Icon className="w-5 h-5 text-amber-600" />
                                {action.confirmTitle}
                              </DialogTitle>
                              <DialogDescription className="leading-relaxed pt-2 max-w-prose">
                                {action.confirmMsg}
                              </DialogDescription>
                            </DialogHeader>
                            <div className="bg-amber-50 p-4 rounded-lg border-l-4 border-amber-400">
                              <div className="flex items-start gap-2">
                                <AlertTriangle className="w-4 h-4 text-amber-600 mt-0.5 flex-shrink-0" />
                                <p className="text-sm text-amber-800 leading-relaxed">
                                  <strong>Warning:</strong> This operation cannot be reversed. The system will return to its initial empty state.
                                </p>
                              </div>
                            </div>
                            <DialogFooter className="gap-2">
                              <Button
                                variant="outline"
                                onClick={() => setDialogOpen(null)}
                                disabled={isLoading}
                              >
                                Cancel
                              </Button>
                              <Button
                                variant="destructive"
                                onClick={() => run(action.id)}
                                disabled={isLoading}
                                className="bg-gradient-to-r from-amber-600 to-orange-600 hover:from-amber-700 hover:to-orange-700"
                              >
                                {isLoading ? (
                                  <>
                                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                                    Processing...
                                  </>
                                ) : (
                                  <>
                                    <Icon className="w-4 h-4 mr-2" />
                                    Confirm {action.title}
                                  </>
                                )}
                              </Button>
                            </DialogFooter>
                          </DialogContent>
                        </Dialog>
                      </CardContent>
                    </Card>
                  );
                })}
              </div>
            </div>

            {/* Standard Actions */}
            <div>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                {actions.filter(a => a.severity !== 'critical').map((action, index) => {
                  const Icon = action.icon;
                  const isLoading = loading[action.id];

                  return (
                    <motion.div
                      key={action.id}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.5, delay: index * 0.1 }}
                      className="py-1"
                    >
                      <Card className={`h-full flex flex-col group hover:shadow-2xl transition-all duration-300 hover:-translate-y-1 border ${action.borderColor} bg-gradient-to-br ${action.bgColor} backdrop-blur-sm`}>
                        <CardHeader className="pb-6">
                          <div className="flex items-center justify-between mb-4">
                            <div className={`inline-flex w-14 h-14 items-center justify-center rounded-2xl ${action.color} bg-white border-2 ${action.borderColor} group-hover:scale-110 transition-transform shadow-sm`}>
                              <Icon className="w-7 h-7" />
                            </div>
                            <Badge
                              variant="outline"
                              className="text-xs font-medium"
                            >
                              ⚡
                            </Badge>
                          </div>
                          <CardTitle className={`text-xl font-bold ${action.color} group-hover:opacity-80 transition-opacity`}>
                            {action.title}
                          </CardTitle>
                          <CardDescription className="text-base leading-relaxed mt-2">
                            {action.description}
                          </CardDescription>
                        </CardHeader>
                        <CardContent className="pt-0 flex-1 grid grid-rows-[1fr_auto] gap-4">
                          <div className="p-4 bg-white/60 backdrop-blur-sm rounded-xl border border-gray-200/50">
                            <p className="text-sm text-muted-foreground leading-relaxed">
                              {action.detailedDescription}
                            </p>
                          </div>

                          <Dialog open={dialogOpen === action.id} onOpenChange={(open) => setDialogOpen(open ? action.id : null)}>
                            <DialogTrigger asChild>
                              <Button
                                variant={action.buttonVariant}
                                disabled={isAnyLoading}
                                className={`w-full h-12 font-semibold rounded-full shadow-md hover:shadow-xl transition-all duration-300 hover:scale-105 
                        bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white`}
                                size="lg"
                              >
                                {isLoading ? (
                                  <>
                                    <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                                    Processing...
                                  </>
                                ) : (
                                  <>
                                    <Icon className="w-5 h-5 mr-2" />
                                    {action.title}
                                  </>
                                )}
                              </Button>
                            </DialogTrigger>
                            <DialogContent className="max-w-md">
                              <DialogHeader>
                                <DialogTitle className="flex items-center gap-2 text-lg">
                                  <Icon className={`w-5 h-5 ${action.color}`} />
                                  {action.confirmTitle}
                                </DialogTitle>
                                <DialogDescription className="text-base leading-relaxed pt-2">
                                  {action.confirmMsg}
                                </DialogDescription>
                              </DialogHeader>
                              <div className="bg-muted/50 p-4 rounded-lg border-l-4 border-amber-400">
                                <div className="flex items-start gap-2">
                                  <AlertTriangle className="w-4 h-4 text-amber-600 mt-0.5 flex-shrink-0" />
                                  <p className="text-sm text-muted-foreground">
                                    <strong>Important:</strong> This operation cannot be reversed. Make sure you have backups if needed.
                                  </p>
                                </div>
                              </div>
                              <DialogFooter className="gap-2">
                                <Button
                                  variant="outline"
                                  onClick={() => setDialogOpen(null)}
                                  disabled={isLoading}
                                >
                                  Cancel
                                </Button>
                                <Button
                                  variant={action.buttonVariant}
                                  onClick={() => run(action.id)}
                                  disabled={isLoading}
                                >
                                  {isLoading ? (
                                    <>
                                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                                      Processing...
                                    </>
                                  ) : (
                                    <>
                                      <Icon className="w-4 h-4 mr-2" />
                                      Confirm {action.title}
                                    </>
                                  )}
                                </Button>
                              </DialogFooter>
                            </DialogContent>
                          </Dialog>
                        </CardContent>
                      </Card>
                    </motion.div>
                  );
                })}
              </div>
            </div>
          </div>
        </TabsContent>

      </Tabs>
    </motion.div>
  );
}
