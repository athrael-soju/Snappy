"use client";

import Link from "next/link";
import { FormEvent, useCallback, useEffect, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Upload,
  FileText,
  Database,
  HardDrive,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  X,
  Sparkles,
  ArrowRight,
  Loader2,
  Wrench,
  ListChecks,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { AppButton } from "@/components/app-button";
import { ScrollArea } from "@/components/ui/scroll-area";
import "@/lib/api/client";
import { useSystemStatus } from "@/stores/app-store";
import { useFileUpload } from "@/lib/hooks/use-file-upload";
import { RoutePageShell } from "@/components/route-page-shell";
import {
  HeroMetaAction,
  HeroMetaGroup,
  HeroMetaPill,
} from "@/components/hero-meta";
import type { UploadFileMeta } from "@/stores/types";

const STATUS_PANEL_AUTO_DISMISS_MS = 4500;

type UploadHelperCard = {
  id: string;
  title: string;
  description: string;
  icon: LucideIcon;
  gradient: string;
  href?: string;
  actionLabel?: string;
};

const UPLOAD_HELPER_CARDS: UploadHelperCard[] = [
  {
    id: "maintenance",
    title: "Let Morty Check System Health",
    description: "Before uploading, Morty recommends verifying that Qdrant and MinIO are ready for your documents.",
    icon: Wrench,
    gradient: "from-chart-2 to-chart-3",
    href: "/maintenance",
    actionLabel: "Open Maintenance",
  },
  {
    id: "prepare",
    title: "Organize for Morty",
    description: "Group related documents together - Morty processes them faster and understands context better this way.",
    icon: ListChecks,
    gradient: "from-chart-4 to-chart-3",
  },
  {
    id: "search",
    title: "Test Morty's Results",
    description: "After Morty indexes your documents, head to Search to see how well he understood your content.",
    icon: Sparkles,
    gradient: "from-chart-1 to-chart-2",
    href: "/search",
    actionLabel: "Go to Search",
  },
];

export default function UploadPage() {
  const { systemStatus, statusLoading, fetchStatus, isReady } = useSystemStatus();
  const {
    files,
    fileMeta,
    uploading,
    uploadProgress,
    message,
    error,
    jobId,
    statusText,
    isDragOver,
    fileCount,
    hasFiles,
    isCancelling,
    handleDragOver,
    handleDragLeave,
    handleDrop,
    handleFileSelect,
    handleUpload,
    handleCancel,
    handleClear,
  } = useFileUpload();

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    await handleUpload(isReady);
  };

  const selectedFiles = files ?? [];
  const persistedFiles =
    uploading && (!selectedFiles || selectedFiles.length === 0) ? fileMeta ?? [] : [];
  const displayFiles: Array<File | UploadFileMeta> =
    selectedFiles && selectedFiles.length > 0 ? selectedFiles : persistedFiles;
  const usingPersistedMeta = selectedFiles.length === 0 && displayFiles.length > 0;
  const showStatusText = Boolean(statusText && statusText !== message);
  const isStatusLoading = uploading && (typeof uploadProgress !== "number" || uploadProgress < 100);

  const [showHelpfulCards, setShowHelpfulCards] = useState(!uploading && !hasFiles);
  const [statusDismissed, setStatusDismissed] = useState(false);
  const dismissTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const clearDismissTimer = useCallback(() => {
    if (dismissTimerRef.current) {
      clearTimeout(dismissTimerRef.current);
      dismissTimerRef.current = null;
    }
  }, []);

  useEffect(() => clearDismissTimer, [clearDismissTimer]);

  const triggerFileDialog = useCallback(() => {
    if (uploading) return;
    fileInputRef.current?.click();
  }, [uploading]);

  useEffect(() => {
    const hasStatusCopy = Boolean(statusText || jobId || message || error);
    const hasVisibleProgress =
      uploading && typeof uploadProgress === "number" && uploadProgress > 0;

    if (uploading || hasFiles) {
      clearDismissTimer();
      setStatusDismissed(false);
      setShowHelpfulCards(false);
      return;
    }

    if (hasStatusCopy || hasVisibleProgress) {
      setStatusDismissed(false);
      setShowHelpfulCards(false);

      if (!dismissTimerRef.current) {
        dismissTimerRef.current = setTimeout(() => {
          setStatusDismissed(true);
          setShowHelpfulCards(true);
          clearDismissTimer();
        }, STATUS_PANEL_AUTO_DISMISS_MS);
      }
    } else {
      clearDismissTimer();
      setStatusDismissed(false);
      setShowHelpfulCards(true);
    }

    return clearDismissTimer;
  }, [
    uploading,
    hasFiles,
    uploadProgress,
    statusText,
    jobId,
    message,
    error,
    clearDismissTimer,
  ]);

  const shouldShowStatusPanel =
    !statusDismissed &&
    Boolean(uploading || statusText || jobId || message || error);

  const shouldShowHelpfulCards = showHelpfulCards && !uploading && !hasFiles;

  const vectorCount =
    typeof systemStatus?.collection?.vector_count === "number"
      ? systemStatus.collection.vector_count.toLocaleString()
      : null;
  const vectorName = systemStatus?.collection?.name ?? null;
  const bucketCount =
    typeof systemStatus?.bucket?.object_count === "number"
      ? systemStatus.bucket.object_count.toLocaleString()
      : null;
  const bucketName = systemStatus?.bucket?.name ?? null;

  const heroMeta = (
    <HeroMetaGroup>
      <HeroMetaPill
        icon={isReady ? CheckCircle2 : AlertCircle}
        tone={isReady ? "success" : "warning"}
      >
        {isReady ? "Ready" : "System not ready"}
      </HeroMetaPill>
      <HeroMetaAction
        onClick={fetchStatus}
        disabled={statusLoading}
        aria-label="Refresh system status"
      >
        {statusLoading ? (
          <>
            <Loader2 className="size-icon-2xs animate-spin" aria-hidden="true" />
            Refreshing
          </>
        ) : (
          <>
            <RefreshCw className="size-icon-2xs" aria-hidden="true" />
            Refresh
          </>
        )}
      </HeroMetaAction>
    </HeroMetaGroup>
  );

  return (
    <RoutePageShell
      eyebrow="Services"
      title="Upload & Index with Morty's Help"
      description="Let Morty guide you through document upload. He'll process your files with advanced visual intelligence and ColPali embeddings."
      meta={heroMeta}
      innerClassName="space-y-6"
      variant="compact"
    >
      <motion.div
        className="flex flex-col space-y-6"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, ease: "easeOut" }}
      >
        {/* Upload Form */}
        <form onSubmit={handleSubmit} className="flex min-h-0 flex-1 flex-col space-y-4">
          {/* Morty's Upload Guide */}
          <motion.div
            className="rounded-2xl border border-vultr-blue/20 bg-gradient-to-r from-vultr-blue/5 to-purple-500/5 p-4"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
          >
            <div className="flex items-center gap-3">
              <div className="flex size-10 items-center justify-center rounded-full bg-vultr-blue/10">
                <motion.div
                  animate={{ rotate: [0, 10, -10, 0] }}
                  transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
                >
                  📄
                </motion.div>
              </div>
              <div>
                <h3 className="text-body-sm font-semibold text-vultr-navy dark:text-white">
                  Morty's Visual Processing Tips
                </h3>
                <p className="text-body-xs text-vultr-navy/70 dark:text-white/70">
                  I work best with clear PDFs, scanned documents, and images with text. The clearer your documents, the better I can help you find what you need! 🤖✨
                </p>
              </div>
            </div>
          </motion.div>

          {/* Drag & Drop Zone */}
          <motion.div
            className={`group relative overflow-hidden rounded-2xl border-2 border-dashed transition-all ${isDragOver
              ? "border-primary bg-primary/5 shadow-xl shadow-primary/25"
              : "border-border/50 bg-card/30 backdrop-blur-sm hover:border-primary/50"
              }`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3, duration: 0.4 }}
            whileHover={{ scale: 1.01 }}
            whileTap={{ scale: 0.99 }}
          >
            <div className={`absolute inset-0 bg-gradient-to-br from-chart-1 to-chart-2 opacity-0 transition-opacity ${isDragOver ? "opacity-10" : "group-hover:opacity-5"}`} />

            <div className="relative flex min-h-[200px] flex-col items-center justify-center gap-4 p-6 sm:p-8">
              <div className="flex h-14 w-14 items-center justify-center rounded-xl bg-gradient-to-br from-chart-1 to-chart-2 shadow-lg">
                <Upload className="h-7 w-7 text-primary-foreground" />
              </div>

              <div className="text-center space-y-2">
                <h3 className="text-body font-bold">
                  {isDragOver ? "Morty's ready! Drop files here" : "Share your documents with Morty"}
                </h3>
                <p className="text-body-sm text-muted-foreground">
                  or browse • Morty loves PDFs, images, and documents! 📄✨
                </p>
              </div>

              <div className="flex items-center gap-2">
                <AppButton
                  type="button"
                  variant="outline"
                  size="md"
                  onClick={triggerFileDialog}
                  disabled={uploading}
                >
                  <FileText className="size-icon-xs" />
                  Browse Files
                </AppButton>

                {hasFiles && (
                  <>
                    <AppButton
                      type="submit"
                      size="md"
                      elevated
                      disabled={!hasFiles || uploading || !isReady}
                    >
                      {uploading ? (
                        <>
                          <Loader2 className="size-icon-xs animate-spin" />
                          <span className="hidden sm:inline">Uploading...</span>
                        </>
                      ) : (
                        <>
                          <Upload className="size-icon-xs" />
                          <span className="hidden sm:inline">Upload</span>
                        </>
                      )}
                    </AppButton>

                    {uploading && (
                      <AppButton
                        type="button"
                        onClick={handleCancel}
                        size="md"
                        variant="ghost"
                        disabled={isCancelling}
                      >
                        <X className="size-icon-xs" />
                        <span className="hidden sm:inline">
                          {isCancelling ? "Cancelling..." : "Cancel"}
                        </span>
                      </AppButton>
                    )}
                  </>
                )}
              </div>

              <input
                id="file-input"
                type="file"
                multiple
                ref={fileInputRef}
                onChange={(event) => {
                  handleFileSelect(event.target.files);
                  if (event.target) {
                    event.target.value = "";
                  }
                }}
                disabled={uploading}
                className="hidden"
              />
            </div>
          </motion.div>

          {/* Selected Files */}
          <AnimatePresence mode="wait">
            {hasFiles && (
              <motion.div
                className="flex min-h-0 flex-1 flex-col rounded-xl border border-border/50 bg-card/50 p-3 backdrop-blur-sm"
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                exit={{ opacity: 0, height: 0 }}
                transition={{ duration: 0.3 }}
              >
                <div className="mb-2 flex shrink-0 items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <Sparkles className="size-icon-xs text-primary" />
                    <h3 className="text-body-sm font-bold">
                      Ready to Upload ({fileCount} {fileCount === 1 ? "file" : "files"})
                    </h3>
                  </div>
                  <AppButton
                    type="button"
                    onClick={() => {
                      handleClear();
                      if (fileInputRef.current) {
                        fileInputRef.current.value = "";
                      }
                    }}
                    size="xs"
                    variant="ghost"
                    disabled={uploading}
                  >
                    <X className="size-icon-3xs" />
                    Clear
                  </AppButton>
                </div>

                <ScrollArea className="h-[20vh] w-full max-w-6xl mx-auto">
                  {usingPersistedMeta && (
                    <p className="mb-2 px-1 text-body-xs text-muted-foreground">
                      Upload resuming after refresh. You can still monitor progress or cancel while the server finishes.
                    </p>
                  )}
                  <div className="space-y-1.5 pr-4">
                    {displayFiles.map((file, index) => {
                      const isFileObject = file instanceof File;
                      const keyBase = isFileObject ? `${file.lastModified}` : "meta";
                      const fileKey = `${file.name}-${keyBase}-${index}`;
                      const sizeKb = (file.size / 1024).toFixed(1);

                      return (
                        <motion.div
                          key={fileKey}
                          className="flex items-center justify-between rounded-lg border border-border/50 bg-background/50 px-3 py-2.5 transition-colors hover:bg-muted/50"
                          initial={{ opacity: 0, x: -20 }}
                          animate={{ opacity: 1, x: 0 }}
                          exit={{ opacity: 0, x: 20 }}
                          transition={{ delay: index * 0.05, duration: 0.2 }}
                          whileHover={{ scale: 1.02, x: 4 }}
                        >
                          <div className="flex items-center gap-2 min-w-0">
                            <FileText className="size-icon-xs shrink-0 text-primary" />
                            <div className="min-w-0">
                              <p className="truncate text-body-xs font-medium">{file.name}</p>
                              <p className="text-body-xs text-muted-foreground">{sizeKb} KB</p>
                            </div>
                          </div>
                        </motion.div>
                      );
                    })}
                  </div>
                </ScrollArea>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Progress & Status Messages */}
          <AnimatePresence mode="wait">
            {shouldShowStatusPanel && (
              <motion.div
                className="space-y-2 rounded-xl border border-border/50 bg-card/50 p-4 backdrop-blur-sm"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                transition={{ duration: 0.3 }}
              >
                {uploading && (typeof uploadProgress !== "number" || uploadProgress === 0) && !statusText && (
                  <div className="flex items-center gap-2 rounded-lg bg-muted/40 px-3 py-2 text-body-xs text-muted-foreground">
                    <Loader2 className="size-icon-3xs animate-spin" />
                    Preparing upload...
                  </div>
                )}

                {uploading && typeof uploadProgress === "number" && uploadProgress > 0 && (
                  <div className="space-y-1.5">
                    <div className="flex items-center justify-between text-body-xs">
                      <span className="font-medium">Upload Progress</span>
                      <span className="font-semibold text-primary">{Math.round(uploadProgress)}%</span>
                    </div>
                    <div className="h-2 overflow-hidden rounded-full bg-muted">
                      <div
                        className="h-full bg-gradient-to-r from-chart-1 to-chart-2 transition-all duration-300"
                        style={{ width: `${uploadProgress}%` }}
                      />
                    </div>
                  </div>
                )}

                {showStatusText && (
                  <div className="flex items-center gap-2 text-body-xs text-muted-foreground">
                    {isStatusLoading ? (
                      <Loader2 className="size-icon-3xs animate-spin" />
                    ) : error ? (
                      <AlertCircle className="size-icon-3xs text-destructive" />
                    ) : (
                      <CheckCircle2 className="size-icon-3xs text-chart-2" />
                    )}
                    {statusText}
                  </div>
                )}

                {jobId && (
                  <div className="rounded-lg bg-muted/50 px-2 py-1.5">
                    <p className="text-body-xs text-muted-foreground">
                      Job ID: <span className="font-mono">{jobId}</span>
                    </p>
                  </div>
                )}

                <AnimatePresence initial={false} mode="sync">
                  {message && (
                    <motion.div
                      key="upload-success"
                      initial={{ opacity: 0, y: 6 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -6 }}
                      transition={{ duration: 0.25, ease: "easeInOut" }}
                      className="flex items-center gap-2 rounded-lg bg-chart-2/10 px-3 py-2 text-body-xs font-medium text-chart-2 dark:text-chart-2"
                    >
                      <CheckCircle2 className="size-icon-xs" />
                      {message}
                    </motion.div>
                  )}
                </AnimatePresence>

                <AnimatePresence initial={false} mode="sync">
                  {error && (
                    <motion.div
                      key="upload-error"
                      initial={{ opacity: 0, y: 6 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -6 }}
                      transition={{ duration: 0.25, ease: "easeInOut" }}
                      className="flex items-center gap-2 rounded-lg bg-destructive/10 px-3 py-2 text-body-xs font-medium text-destructive dark:text-destructive"
                    >
                      <AlertCircle className="size-icon-xs" />
                      {error}
                    </motion.div>
                  )}
                </AnimatePresence>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Helpful Guidance */}
          <AnimatePresence mode="wait">
            {shouldShowHelpfulCards && (
              <motion.section
                className="space-y-3 rounded-2xl border border-border/50 bg-card/40 p-4 backdrop-blur-sm"
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -12 }}
                transition={{ duration: 0.3 }}
              >
                <div className="flex items-center gap-2">
                  <Sparkles className="size-icon-xs text-primary" />
                  <h3 className="text-body font-bold">Morty's Working His Magic ✨</h3>
                </div>

                <div className="grid gap-3 sm:grid-cols-3">
                  {UPLOAD_HELPER_CARDS.map((card, index) => (
                    <motion.article
                      key={card.id}
                      className="group relative overflow-hidden rounded-xl border border-border/50 bg-background/60 p-4 transition-all hover:border-primary/50 hover:shadow-lg hover:shadow-primary/10"
                      initial={{ opacity: 0, y: 12 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.05, duration: 0.25 }}
                      whileHover={{ y: -4, scale: 1.01 }}
                      whileTap={{ scale: 0.99 }}
                    >
                      <div className={`absolute inset-0 bg-gradient-to-br ${card.gradient} opacity-0 transition-opacity group-hover:opacity-10`} />
                      <div className="relative space-y-3">
                        <div className="flex items-center gap-2">
                          <div className="flex size-10 items-center justify-center rounded-lg bg-muted/70">
                            <card.icon className="size-icon-xs text-primary" />
                          </div>
                          <h4 className="text-body-sm font-semibold">{card.title}</h4>
                        </div>
                        <p className="text-body-xs text-muted-foreground">{card.description}</p>
                        {card.href && card.actionLabel && (
                          <Link
                            href={card.href}
                            className="inline-flex items-center gap-1 text-body-xs font-semibold text-primary transition-colors hover:text-primary/80"
                          >
                            {card.actionLabel}
                            <ArrowRight className="size-icon-3xs" />
                          </Link>
                        )}
                      </div>
                    </motion.article>
                  ))}
                </div>
              </motion.section>
            )}
          </AnimatePresence>

        </form>
      </motion.div>
    </RoutePageShell>
  );
}
