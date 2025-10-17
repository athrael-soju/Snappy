"use client";

import "@/lib/api/client";
import { useSystemStatus, useMaintenanceActions, useSystemManagement } from "@/lib/hooks";
import { useState } from "react";
import { 
  Wrench, 
  Database, 
  HardDrive, 
  Play, 
  Trash2, 
  RefreshCw,
  AlertCircle,
  CheckCircle2,
  Loader2,
  Server,
  Zap,
  ShieldAlert
} from "lucide-react";
import type { ActionType } from "@/lib/hooks/use-maintenance-actions";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";

const CORE_OPERATIONS = [
  {
    id: "initialize",
    title: "Initialize Storage",
    description: "Prepare the Qdrant collection and optionally the MinIO bucket for data storage.",
    icon: Play,
    gradient: "from-chart-1 to-chart-2"
  },
  {
    id: "delete",
    title: "Delete Storage",
    description: "Permanently remove the collection and bucket resources from the system.",
    icon: Trash2,
    gradient: "from-chart-4 to-chart-3"
  },
  {
    id: "reset",
    title: "Reset All Data",
    description: "Remove every stored document, embedding, and image from the entire system.",
    icon: ShieldAlert,
    gradient: "from-destructive to-destructive/80"
  }
];

export default function MaintenancePage() {
  const { systemStatus, statusLoading, fetchStatus, isSystemReady } = useSystemStatus();
  const { loading, runAction } = useMaintenanceActions({ onSuccess: fetchStatus });
  const { initLoading, deleteLoading, handleInitialize, handleDelete } = useSystemManagement({ onSuccess: fetchStatus });
  
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [resetDialogOpen, setResetDialogOpen] = useState(false);

  const handleResetAll = () => {
    void runAction("all");
    setResetDialogOpen(false);
  };

  const confirmDelete = () => {
    void handleDelete();
    setDeleteDialogOpen(false);
  };

  return (
    <div className="relative flex min-h-full flex-col overflow-hidden">
      <ScrollArea className="flex-1">
        <div className="px-4 py-6 sm:px-6 lg:px-8">
          <div className="mx-auto w-full max-w-5xl space-y-4">
          {/* Header Section */}
          <div className="space-y-2 text-center">
            <h1 className="text-xl font-bold tracking-tight sm:text-2xl lg:text-3xl">
              <span className="bg-gradient-to-br from-foreground via-foreground to-foreground/70 bg-clip-text text-transparent">
                System
              </span>
              {" "}
              <span className="bg-gradient-to-r from-destructive via-destructive/80 to-destructive bg-clip-text text-transparent">
                Maintenance
              </span>
            </h1>
            
            <p className="mx-auto max-w-2xl text-xs leading-relaxed text-muted-foreground">
              Monitor storage status and run maintenance operations. Handle destructive actions with care.
            </p>

            <div className="flex flex-wrap items-center justify-center gap-2 pt-2">
              <Badge 
                variant={isSystemReady ? "default" : "destructive"}
                className="gap-1.5 px-3 py-1"
              >
                {isSystemReady ? (
                  <>
                    <CheckCircle2 className="h-3 w-3" />
                    System Ready
                  </>
                ) : (
                  <>
                    <AlertCircle className="h-3 w-3" />
                    Not Ready
                  </>
                )}
              </Badge>
              
              <Button
                onClick={fetchStatus}
                disabled={statusLoading}
                variant="ghost"
                size="sm"
                className="h-8 gap-1.5 rounded-full px-4 text-xs touch-manipulation"
              >
                {statusLoading ? (
                  <Loader2 className="h-3 w-3 animate-spin" />
                ) : (
                  <RefreshCw className="h-3 w-3" />
                )}
                Refresh
              </Button>
            </div>
          </div>

          {/* Storage Status */}
          <section className="space-y-3">
              <div className="flex items-center gap-2">
                <Server className="h-5 w-5 text-primary" />
                <h2 className="text-lg font-bold">Storage Status</h2>
              </div>
              
              <div className="grid gap-3 sm:grid-cols-2">
                <article className="group relative overflow-hidden rounded-xl border border-border/50 bg-card/50 p-4 backdrop-blur-sm transition-all hover:border-primary/50 hover:shadow-lg hover:shadow-primary/10 touch-manipulation">
                  <div className="absolute inset-0 bg-gradient-to-br from-chart-2 to-chart-3 opacity-0 transition-opacity group-hover:opacity-5" />
                  
                  <div className="relative space-y-3">
                    <div className="flex items-center gap-2">
                      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-chart-2 to-chart-3 shadow-lg sm:h-10 sm:w-10">
                        <Database className="h-4 w-4 text-primary-foreground sm:h-5 sm:w-5" />
                      </div>
                      <h3 className="min-w-0 flex-1 truncate text-sm sm:text-base font-bold">Qdrant Collection</h3>
                    </div>
                    
                    {statusLoading ? (
                      <div className="flex items-center gap-2 text-xs text-muted-foreground">
                        <Loader2 className="h-3 w-3 animate-spin" />
                        Loading...
                      </div>
                    ) : systemStatus?.collection ? (
                      <div className="space-y-2">
                        <div className="flex flex-wrap gap-2">
                          <Badge variant="outline" className="text-xs">
                            {systemStatus.collection.name}
                          </Badge>
                          <Badge 
                            variant={systemStatus.collection.exists ? "default" : "destructive"}
                            className="gap-1 text-xs"
                          >
                            {systemStatus.collection.exists ? (
                              <><CheckCircle2 className="h-3 w-3 text-chart-2" /> Exists</>
                            ) : (
                              <><AlertCircle className="h-3 w-3" /> Not Found</>
                            )}
                          </Badge>
                        </div>
                        <div className="grid grid-cols-2 gap-2 text-xs">
                          <div className="rounded-lg bg-muted/50 px-2 py-1.5">
                            <p className="text-muted-foreground">Vectors</p>
                            <p className="font-semibold">{systemStatus.collection.vector_count?.toLocaleString() ?? 0}</p>
                          </div>
                          <div className="rounded-lg bg-muted/50 px-2 py-1.5">
                            <p className="text-muted-foreground">Files</p>
                            <p className="font-semibold">{systemStatus.collection.unique_files?.toLocaleString() ?? 0}</p>
                          </div>
                        </div>
                        {systemStatus.collection.error && (
                          <div className="flex items-center gap-2 rounded-lg bg-destructive/10 px-2 py-1.5 text-xs text-destructive">
                            <AlertCircle className="h-3 w-3" />
                            {systemStatus.collection.error}
                          </div>
                        )}
                      </div>
                    ) : (
                      <p className="text-xs text-muted-foreground">No information available.</p>
                    )}
                  </div>
                </article>

                <article className="group relative overflow-hidden rounded-xl border border-border/50 bg-card/50 p-4 backdrop-blur-sm transition-all hover:border-primary/50 hover:shadow-lg hover:shadow-primary/10 touch-manipulation">
                  <div className="absolute inset-0 bg-gradient-to-br from-chart-4 to-chart-3 opacity-0 transition-opacity group-hover:opacity-5" />
                  
                  <div className="relative space-y-3">
                    <div className="flex items-center gap-2">
                      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-chart-4 to-chart-3 shadow-lg sm:h-10 sm:w-10">
                        <HardDrive className="h-4 w-4 text-primary-foreground sm:h-5 sm:w-5" />
                      </div>
                      <h3 className="min-w-0 flex-1 truncate text-sm sm:text-base font-bold">MinIO Bucket</h3>
                    </div>
                    
                    {statusLoading ? (
                      <div className="flex items-center gap-2 text-xs text-muted-foreground">
                        <Loader2 className="h-3 w-3 animate-spin" />
                        Loading...
                      </div>
                    ) : systemStatus?.bucket ? (
                      <div className="space-y-2">
                        <div className="flex flex-wrap gap-2">
                          <Badge variant="outline" className="text-xs">
                            {systemStatus.bucket.name}
                          </Badge>
                          <Badge 
                            variant={systemStatus.bucket.exists && !systemStatus.bucket.disabled ? "default" : "destructive"}
                            className="gap-1 text-xs"
                          >
                            {systemStatus.bucket.exists && !systemStatus.bucket.disabled ? (
                              <><CheckCircle2 className="h-3 w-3 text-chart-2" /> Active</>
                            ) : systemStatus.bucket.disabled ? (
                              <><AlertCircle className="h-3 w-3" /> Disabled</>
                            ) : (
                              <><AlertCircle className="h-3 w-3" /> Not Found</>
                            )}
                          </Badge>
                        </div>
                        <div className="grid grid-cols-2 gap-2 text-xs">
                          <div className="rounded-lg bg-muted/50 px-2 py-1.5">
                            <p className="text-muted-foreground">Objects</p>
                            <p className="font-semibold">{systemStatus.bucket.object_count?.toLocaleString() ?? 0}</p>
                          </div>
                          <div className="rounded-lg bg-muted/50 px-2 py-1.5">
                            <p className="text-muted-foreground">Status</p>
                            <p className="font-semibold">{systemStatus.bucket.disabled ? "Disabled" : "Enabled"}</p>
                          </div>
                        </div>
                        {systemStatus.bucket.error && (
                          <div className="flex items-center gap-2 rounded-lg bg-destructive/10 px-2 py-1.5 text-xs text-destructive">
                            <AlertCircle className="h-3 w-3" />
                            {systemStatus.bucket.error}
                          </div>
                        )}
                      </div>
                    ) : (
                      <p className="text-xs text-muted-foreground">No information available.</p>
                    )}
                  </div>
                </article>
              </div>
            </section>

            {/* Core Operations */}
            <section className="space-y-3">
              <div className="flex items-center gap-2">
                <Wrench className="h-5 w-5 text-primary" />
                <h2 className="text-lg font-bold">Core Operations</h2>
              </div>
              
              <p className="text-xs leading-relaxed text-muted-foreground">
                Manage system storage and data lifecycle. Each action requires confirmation and may be irreversible.
              </p>
              
              <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
                {CORE_OPERATIONS.map((operation) => {
                  const Icon = operation.icon;
                  const isLoading = 
                    (operation.id === "initialize" && initLoading) ||
                    (operation.id === "delete" && deleteLoading) ||
                    (operation.id === "reset" && loading["all"]);
                  const isDisabled = initLoading || deleteLoading || loading["all"];
                  
                  const handleClick = () => {
                    if (operation.id === "initialize") {
                      void handleInitialize();
                    } else if (operation.id === "delete") {
                      setDeleteDialogOpen(true);
                    } else if (operation.id === "reset") {
                      setResetDialogOpen(true);
                    }
                  };
                  
                  return (
                    <article 
                      key={operation.id}
                      className="group relative overflow-hidden rounded-xl border border-border/50 bg-card/50 p-4 sm:p-5 backdrop-blur-sm transition-all hover:border-primary/50 hover:shadow-lg hover:shadow-primary/10 touch-manipulation"
                    >
                      <div className={`absolute inset-0 bg-gradient-to-br ${operation.gradient} opacity-0 transition-opacity group-hover:opacity-5`} />
                      
                      <div className="relative space-y-3">
                        <div className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-gradient-to-br ${operation.gradient} shadow-lg sm:h-10 sm:w-10`}>
                          <Icon className="h-4 w-4 text-primary-foreground sm:h-5 sm:w-5" />
                        </div>
                        <div className="space-y-1.5">
                          <h3 className="text-sm sm:text-base font-bold">{operation.title}</h3>
                          <p className="text-xs sm:text-sm leading-relaxed text-muted-foreground">{operation.description}</p>
                        </div>
                        <Button
                          type="button"
                          onClick={handleClick}
                          disabled={isDisabled}
                          variant={operation.id === "reset" ? "destructive" : operation.id === "delete" ? "outline" : "default"}
                          size="sm"
                          className="w-full h-10 gap-2 rounded-full touch-manipulation"
                        >
                          {isLoading ? (
                            <>
                              <Loader2 className="h-4 w-4 animate-spin" />
                              {operation.id === "initialize" ? "Initializing..." : 
                               operation.id === "delete" ? "Deleting..." : "Resetting..."}
                            </>
                          ) : (
                            <>
                              <Icon className="h-4 w-4" />
                              {operation.id === "initialize" ? "Initialize" : 
                               operation.id === "delete" ? "Delete" : "Reset All"}
                            </>
                          )}
                        </Button>
                      </div>
                    </article>
                  );
                })}
              </div>
            </section>
          </div>
        </div>
      </ScrollArea>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent className="border-destructive/50 bg-card/95 backdrop-blur-xl">
          <AlertDialogHeader>
            <div className="flex items-center gap-2">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-destructive/10">
                <Trash2 className="h-5 w-5 text-destructive" />
              </div>
              <AlertDialogTitle className="text-xl">Delete Storage?</AlertDialogTitle>
            </div>
            <AlertDialogDescription className="pt-2 text-sm leading-relaxed">
              This will permanently delete the collection and (if enabled) the bucket. All vectors, metadata, and stored images will be removed. This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter className="gap-2 sm:gap-2">
            <AlertDialogCancel className="h-10 rounded-full touch-manipulation">Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={confirmDelete}
              className="h-10 gap-2 rounded-full bg-destructive text-destructive-foreground shadow-lg hover:bg-destructive/90 touch-manipulation"
            >
              <Trash2 className="h-4 w-4" />
              Delete Storage
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Reset Confirmation Dialog */}
      <AlertDialog open={resetDialogOpen} onOpenChange={setResetDialogOpen}>
        <AlertDialogContent className="border-destructive/50 bg-card/95 backdrop-blur-xl">
          <AlertDialogHeader>
            <div className="flex items-center gap-2">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-destructive/10">
                <ShieldAlert className="h-5 w-5 text-destructive" />
              </div>
              <AlertDialogTitle className="text-xl">Reset Entire System?</AlertDialogTitle>
            </div>
            <AlertDialogDescription className="pt-2 text-sm leading-relaxed">
              This will permanently remove <strong className="font-semibold text-foreground">all data</strong> from your system including all documents, embeddings, and images. The storage infrastructure will remain but will be completely empty. This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter className="gap-2 sm:gap-2">
            <AlertDialogCancel className="h-10 rounded-full touch-manipulation">Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleResetAll}
              className="h-10 gap-2 rounded-full bg-destructive text-destructive-foreground shadow-lg hover:bg-destructive/90 touch-manipulation"
            >
              <ShieldAlert className="h-4 w-4" />
              Reset Everything
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
