"use client";

import { motion, AnimatePresence } from "framer-motion";
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
  ShieldAlert,
} from "lucide-react";
import { AppButton } from "@/components/app-button";
import { Badge } from "@/components/ui/badge";
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
import { cn } from "@/lib/utils";
import { RoutePageShell } from "@/components/route-page-shell";

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
  const badgeBase = "rounded-full border px-3 py-1 text-body-xs font-semibold";
  const badgeClasses = {
    neutral: cn(badgeBase, "border-border/40 bg-muted/70 text-muted-foreground"),
    positive: cn(badgeBase, "border-chart-2/40 bg-chart-2/10 text-chart-2"),
    negative: cn(badgeBase, "border-destructive/40 bg-destructive/10 text-destructive"),
    warning: cn(badgeBase, "border-amber-400/40 bg-amber-500/10 text-amber-200"),
  };

  const handleResetAll = () => {
    void runAction("all");
    setResetDialogOpen(false);
  };

  const confirmDelete = () => {
    void handleDelete();
    setDeleteDialogOpen(false);
  };

  const vectorCount =
    typeof systemStatus?.collection?.vector_count === "number"
      ? systemStatus.collection.vector_count.toLocaleString()
      : null;
  const bucketCount =
    typeof systemStatus?.bucket?.object_count === "number"
      ? systemStatus.bucket.object_count.toLocaleString()
      : null;
  const vectorName = systemStatus?.collection?.name ?? null;
  const bucketName = systemStatus?.bucket?.name ?? null;

  const heroActions = (
    <>
      <AppButton
        type="button"
        onClick={() => void handleInitialize()}
        disabled={initLoading || statusLoading}
        variant="primary"
        size="sm"
        className="rounded-[var(--radius-button)] px-5"
      >
        {initLoading ? (
          <>
            <Loader2 className="size-icon-2xs animate-spin" />
            Initializing...
          </>
        ) : (
          <>
            <Play className="size-icon-2xs" />
            Initialize storage
          </>
        )}
      </AppButton>
      <AppButton
        type="button"
        onClick={() => fetchStatus()}
        disabled={statusLoading}
        variant="outline"
        size="sm"
        className="rounded-[var(--radius-button)]"
      >
        {statusLoading ? <Loader2 className="size-icon-2xs animate-spin" /> : <RefreshCw className="size-icon-2xs" />}
        Refresh status
      </AppButton>
    </>
  );

  return (
    <>
      <RoutePageShell
        eyebrow="Operations"
        title="System Maintenance"
        description="Monitor storage health, verify resource readiness, and run core maintenance operations."
        actions={heroActions}
        variant="compact"
      >
        <div className="px-4 py-6 sm:px-6 lg:px-8">
          <motion.div
            className="mx-auto w-full max-w-5xl space-y-4"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, ease: "easeOut" }}
          >
            <motion.section
              className="space-y-3 rounded-3xl border border-border/30 bg-card/10 p-5 shadow-sm backdrop-blur-sm"
              initial={{ opacity: 0, scale: 0.97 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.15, duration: 0.3 }}
            >
              <div className="flex items-center gap-2">
                <Server className="size-icon-md text-primary" />
                <h2 className="text-digital-h5 font-semibold">Storage status</h2>
              </div>

              <div className="grid gap-3 sm:grid-cols-2">
                <motion.article
                  className="group relative overflow-hidden rounded-xl border border-border/50 bg-card/50 p-4 backdrop-blur-sm transition-all hover:border-primary/50 hover:shadow-lg hover:shadow-primary/10 touch-manipulation"
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.3, duration: 0.3 }}
                  whileHover={{ scale: 1.02, y: -2 }}
                  whileTap={{ scale: 0.98 }}
                >
                  <div className="absolute inset-0 bg-gradient-to-br from-chart-2 to-chart-3 opacity-0 transition-opacity group-hover:opacity-5" />

                  <div className="relative space-y-3">
                    <div className="flex items-center gap-2">
                      <div className="flex size-icon-xl shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-chart-2 to-chart-3 shadow-lg sm:size-icon-2xl">
                        <Database className="size-icon-xs text-primary-foreground sm:size-icon-md" />
                      </div>
                      <h3 className="min-w-0 flex-1 truncate text-body-sm sm:text-body font-bold">Qdrant Collection</h3>
                    </div>

                    {statusLoading ? (
                      <div className="flex items-center gap-2 text-body-xs text-muted-foreground">
                        <Loader2 className="size-icon-3xs animate-spin" />
                        Loading...
                      </div>
                    ) : systemStatus?.collection ? (
                      <div className="space-y-2">
                        <div className="flex flex-wrap gap-2">
                          <Badge variant="outline" className={badgeClasses.neutral}>
                            {systemStatus.collection.name}
                          </Badge>
                          <Badge
                            variant="outline"
                            className={cn("gap-1", systemStatus.collection.exists ? badgeClasses.positive : badgeClasses.negative)}
                          >
                            {systemStatus.collection.exists ? (
                              <><CheckCircle2 className="size-icon-3xs" /> Active</>
                            ) : (
                              <><AlertCircle className="size-icon-3xs" /> Not Found</>
                            )}
                          </Badge>
                          {typeof systemStatus.collection.embedded === "boolean" && (
                            <Badge
                              variant="outline"
                              className={cn(
                                "gap-1.5",
                                systemStatus.collection.embedded ? badgeClasses.positive : badgeClasses.neutral
                              )}
                            >
                              {systemStatus.collection.embedded ? (
                                <>
                                  <Zap className="size-icon-3xs" />
                                  Embedded
                                </>
                              ) : (
                                <>
                                  <Server className="size-icon-3xs" />
                                  Container
                                </>
                              )}
                            </Badge>
                          )}
                        </div>
                        <div className="grid grid-cols-2 gap-2 text-body-xs">
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
                          <div className="flex items-center gap-2 rounded-lg bg-destructive/10 px-2 py-1.5 text-body-xs text-destructive">
                            <AlertCircle className="size-icon-3xs" />
                            {systemStatus.collection.error}
                          </div>
                        )}
                      </div>
                    ) : (
                      <p className="text-body-xs text-muted-foreground">No information available.</p>
                    )}
                  </div>
                </motion.article>

                <motion.article
                  className="group relative overflow-hidden rounded-xl border border-border/50 bg-card/50 p-4 backdrop-blur-sm transition-all hover:border-primary/50 hover:shadow-lg hover:shadow-primary/10 touch-manipulation"
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.3, duration: 0.3 }}
                  whileHover={{ scale: 1.02, y: -2 }}
                  whileTap={{ scale: 0.98 }}
                >
                  <div className="absolute inset-0 bg-gradient-to-br from-chart-4 to-chart-3 opacity-0 transition-opacity group-hover:opacity-5" />

                  <div className="relative space-y-3">
                    <div className="flex items-center gap-2">
                      <div className="flex size-icon-xl shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-chart-4 to-chart-3 shadow-lg sm:size-icon-2xl">
                        <HardDrive className="size-icon-xs text-primary-foreground sm:size-icon-md" />
                      </div>
                      <h3 className="min-w-0 flex-1 truncate text-body-sm sm:text-body font-bold">MinIO Bucket</h3>
                    </div>

                    {statusLoading ? (
                      <div className="flex items-center gap-2 text-body-xs text-muted-foreground">
                        <Loader2 className="size-icon-3xs animate-spin" />
                        Loading...
                      </div>
                    ) : systemStatus?.bucket ? (
                      <div className="space-y-2">
                        <div className="flex flex-wrap gap-2">
                          <Badge variant="outline" className={badgeClasses.neutral}>
                            {systemStatus.bucket.name}
                          </Badge>
                          <Badge
                            variant="outline"
                            className={cn(
                              "gap-1",
                              systemStatus.bucket.exists ? badgeClasses.positive : badgeClasses.negative
                            )}
                          >
                            {systemStatus.bucket.exists ? (
                              <><CheckCircle2 className="size-icon-3xs" /> Active</>
                            ) : (
                              <><AlertCircle className="size-icon-3xs" /> Not Found</>
                            )}
                          </Badge>
                        </div>
                        <div className="grid grid-cols-2 gap-2 text-body-xs">
                          <div className="rounded-lg bg-muted/50 px-2 py-1.5">
                            <p className="text-muted-foreground">Objects</p>
                            <p className="font-semibold">{systemStatus.bucket.object_count?.toLocaleString() ?? 0}</p>
                          </div>
                          <div className="rounded-lg bg-muted/50 px-2 py-1.5">
                            <p className="text-muted-foreground">Status</p>
                            <p className="font-semibold">{systemStatus.bucket.exists ? "Available" : "Unavailable"}</p>
                          </div>
                        </div>
                        {systemStatus.bucket.error && (
                          <div className="flex items-center gap-2 rounded-lg bg-destructive/10 px-2 py-1.5 text-body-xs text-destructive">
                            <AlertCircle className="size-icon-3xs" />
                            {systemStatus.bucket.error}
                          </div>
                        )}
                      </div>
                    ) : (
                      <p className="text-body-xs text-muted-foreground">No information available.</p>
                    )}
                  </div>
                </motion.article>
              </div>
            </motion.section>

            {/* Core Operations */}
            <motion.section
              className="space-y-3"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4, duration: 0.3 }}
            >
              <div className="flex items-center gap-2">
                <Wrench className="size-icon-md text-primary" />
                <h2 className="text-digital-h5 font-semibold">Core Operations</h2>
              </div>

              <p className="text-body-xs leading-relaxed text-muted-foreground">
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
                  const buttonVariant =
                    operation.id === "reset"
                      ? "destructive"
                      : operation.id === "delete"
                        ? "destructive"
                        : "primary";

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
                    <motion.article
                      key={operation.id}
                      className="group relative overflow-hidden rounded-xl border border-border/50 bg-card/50 p-4 sm:p-5 backdrop-blur-sm transition-all hover:border-primary/50 hover:shadow-lg hover:shadow-primary/10 touch-manipulation"
                      initial={{ opacity: 0, scale: 0.9 }}
                      animate={{ opacity: 1, scale: 1 }}
                      transition={{ delay: 0.5 + (CORE_OPERATIONS.findIndex(op => op.id === operation.id) * 0.1), duration: 0.3 }}
                      whileHover={{ scale: 1.03, y: -4 }}
                      whileTap={{ scale: 0.97 }}
                    >
                      <div className={`absolute inset-0 bg-gradient-to-br ${operation.gradient} opacity-0 transition-opacity group-hover:opacity-5`} />

                      <div className="relative space-y-3">
                        <div className={`flex size-icon-xl shrink-0 items-center justify-center rounded-lg bg-gradient-to-br ${operation.gradient} shadow-lg sm:size-icon-2xl`}>
                          <Icon className="size-icon-xs text-primary-foreground sm:size-icon-md" />
                        </div>
                        <div className="space-y-1.5">
                          <h3 className="text-body-sm sm:text-body font-bold">{operation.title}</h3>
                          <p className="text-body-xs sm:text-body-sm leading-relaxed text-muted-foreground">{operation.description}</p>
                        </div>
                        <AppButton
                          type="button"
                          onClick={handleClick}
                          disabled={isDisabled}
                          variant={buttonVariant}
                          size="md"
                          fullWidth
                          elevated
                        >
                          {isLoading ? (
                            <>
                              <Loader2 className="size-icon-xs animate-spin" />
                              {operation.id === "initialize" ? "Initializing..." :
                                operation.id === "delete" ? "Deleting..." : "Resetting..."}
                            </>
                          ) : (
                            <>
                              <Icon className="size-icon-xs" />
                              {operation.id === "initialize" ? "Initialize" :
                                operation.id === "delete" ? "Delete" : "Reset All"}
                            </>
                          )}
                        </AppButton>
                      </div>
                    </motion.article>
                  );
                })}
              </div>
            </motion.section>
          </motion.div>
        </div>
      </RoutePageShell>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent className="border-destructive/50 bg-card/95 backdrop-blur-xl">
          <AlertDialogHeader>
            <div className="flex items-center gap-2">
              <div className="flex size-icon-2xl items-center justify-center rounded-full bg-destructive/10">
                <Trash2 className="size-icon-md text-destructive" />
              </div>
              <AlertDialogTitle className="text-digital-h4 font-semibold text-balance">Delete Storage?</AlertDialogTitle>
            </div>
            <AlertDialogDescription className="pt-2 text-body-sm leading-relaxed">
              This will permanently delete the collection and (if enabled) the bucket. All vectors, metadata, and stored images will be removed. This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter className="gap-2 sm:gap-2">
            <AlertDialogCancel className="h-10 rounded-full touch-manipulation">Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={confirmDelete}
              className="h-10 gap-2 rounded-full bg-destructive text-destructive-foreground shadow-lg hover:bg-destructive/90 touch-manipulation"
            >
              <Trash2 className="size-icon-xs" />
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
              <div className="flex size-icon-2xl items-center justify-center rounded-full bg-destructive/10">
                <ShieldAlert className="size-icon-md text-destructive" />
              </div>
              <AlertDialogTitle className="text-digital-h4 font-semibold text-balance">Reset Entire System?</AlertDialogTitle>
            </div>
            <AlertDialogDescription className="pt-2 text-body-sm leading-relaxed">
              This will permanently remove <strong className="font-semibold text-foreground">all data</strong> from your system including all documents, embeddings, and images. The storage infrastructure will remain but will be completely empty. This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter className="gap-2 sm:gap-2">
            <AlertDialogCancel className="h-10 rounded-full touch-manipulation">Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleResetAll}
              className="h-10 gap-2 rounded-full bg-destructive text-destructive-foreground shadow-lg hover:bg-destructive/90 touch-manipulation"
            >
              <ShieldAlert className="size-icon-xs" />
              Reset Everything
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}
