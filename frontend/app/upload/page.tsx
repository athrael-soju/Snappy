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
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import "@/lib/api/client";
import { useSystemStatus } from "@/stores/app-store";
import { useFileUpload } from "@/lib/hooks/use-file-upload";
import { PageHeader } from "@/components/page-header";
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
    title: "Check System Health",
    description: "Verify the Qdrant collection and MinIO bucket are ready before large uploads.",
    icon: Wrench,
    gradient: "from-chart-2 to-chart-3",
    href: "/maintenance",
    actionLabel: "Open Maintenance",
  },
  {
    id: "prepare",
    title: "Organize Your Files",
    description: "Group related documents together and prefer small batches for faster indexing feedback.",
    icon: ListChecks,
    gradient: "from-chart-4 to-chart-3",
  },
  {
    id: "search",
    title: "Validate Results",
    description: "Head to Search after indexing finishes to spot-check newly embedded content.",
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
    allowedFileTypesLabel,
    maxFilesAllowed,
    maxFileSizeMb,
    fileAccept,
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
    if (uploading || !isReady) return;
    fileInputRef.current?.click();
  }, [uploading, isReady]);

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

  return (
    <div className="relative flex h-full min-h-full flex-col overflow-hidden">
      <div className="flex h-full flex-1 flex-col overflow-hidden px-4 py-6 sm:px-6 lg:px-8">
        <motion.div
          className="mx-auto flex h-full w-full max-w-5xl flex-col space-y-4"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, ease: "easeOut" }}
        >
          {/* Header Section */}
          <motion.div
            className="shrink-0"
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1, duration: 0.3 }}
          >
            <PageHeader
              align="center"
              title={
                <>
                  <span className="bg-gradient-to-br from-foreground via-foreground to-foreground/70 bg-clip-text text-transparent">
                    Upload & Index
                  </span>{" "}
                  <span className="bg-gradient-to-r from-chart-1 via-chart-2 to-chart-1 bg-clip-text text-transparent">
                    Your Documents
                  </span>
                </>
              }
              description="Drop your documents and let Snappy retrieve insights from them."
            />
          </motion.div>

          {/* Compact System Status */}
          <motion.div
            className="flex shrink-0 flex-wrap items-center justify-center gap-2 text-body-xs"
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.2, duration: 0.3 }}
          >
            <Badge
              variant={isReady ? "default" : "destructive"}
              className="gap-1.5 px-3 py-1"
            >
              {isReady ? (
                <>
                  <CheckCircle2 className="size-icon-3xs" />
                  Ready
                </>
              ) : (
                <>
                  <AlertCircle className="size-icon-3xs" />
                  Not Ready
                </>
              )}
            </Badge>

            <Badge variant="outline" className="gap-1.5 px-3 py-1">
              <Database className="size-icon-3xs" />
              <span className="font-semibold">Vectors</span>
              {systemStatus?.collection?.exists ? (
                <CheckCircle2 className="size-icon-3xs text-chart-2" />
              ) : (
                <AlertCircle className="size-icon-3xs text-destructive" />
              )}
              {typeof systemStatus?.collection?.vector_count === "number" && (
                <span className="ml-1 font-semibold">
                  {systemStatus.collection.vector_count.toLocaleString()}
                </span>
              )}
              {systemStatus?.collection?.name && (
                <span className="ml-1 text-[10px] uppercase tracking-wide text-muted-foreground">
                  {systemStatus.collection.name}
                </span>
              )}
            </Badge>

            <Badge variant="outline" className="gap-1.5 px-3 py-1">
              <HardDrive className="size-icon-3xs" />
              <span className="font-semibold">Images</span>
              {systemStatus?.bucket?.exists ? (
                <CheckCircle2 className="size-icon-3xs text-chart-2" />
              ) : (
                <AlertCircle className="size-icon-3xs text-destructive" />
              )}
              {typeof systemStatus?.bucket?.object_count === "number" && (
                <span className="ml-1 font-semibold">
                  {systemStatus.bucket.object_count.toLocaleString()}
                </span>
              )}
              {systemStatus?.bucket?.name && (
                <span className="ml-1 text-[10px] uppercase tracking-wide text-muted-foreground">
                  {systemStatus.bucket.name}
                </span>
              )}
            </Badge>

            <AppButton
              onClick={fetchStatus}
              disabled={statusLoading}
              variant="ghost"
              size="xs"
            >
              {statusLoading ? (
                <Loader2 className="size-icon-3xs animate-spin" />
              ) : (
                <RefreshCw className="size-icon-3xs" />
              )}
              Refresh
            </AppButton>
          </motion.div>

          {/* Upload Form */}
          <form onSubmit={handleSubmit} className="flex min-h-0 flex-1 flex-col space-y-4">
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
                  <h3 className="text-body sm:text-lg font-bold">
                    {isDragOver ? "Drop files here" : "Drag & drop your files"}
                  </h3>
                  <p className="text-body-xs text-muted-foreground">
                    Up to {maxFilesAllowed} ({allowedFileTypesLabel}) files | {maxFileSizeMb} MB each
                  </p>
                </div>

                <div className="flex items-center gap-2">
                  <AppButton
                    type="button"
                    variant="outline"
                    size="md"
                    onClick={triggerFileDialog}
                    disabled={uploading || !isReady}
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
                  accept={fileAccept || undefined}
                  onChange={(event) => {
                    handleFileSelect(event.target.files);
                    if (event.target) {
                      event.target.value = "";
                    }
                  }}
                  disabled={uploading || !isReady}
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

                  <ScrollArea className="min-h-0 flex-1">
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
                            className="flex items-center rounded-lg border border-border/50 bg-background/50 px-3 py-2.5 transition-colors hover:bg-muted/50"
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            exit={{ opacity: 0, x: 20 }}
                            transition={{ delay: index * 0.05, duration: 0.2 }}
                            whileHover={{ scale: 1.02, x: 4 }}
                          >
                            <FileText className="size-icon-xs mr-2 shrink-0 text-primary" />
                            <div className="flex min-w-0 flex-1 items-center justify-between gap-3">
                              <span className="truncate text-body-xs font-medium">
                                {file.name}
                              </span>
                              <span className="whitespace-nowrap text-body-xs text-muted-foreground">
                                {sizeKb} KB
                              </span>
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
                    <h3 className="text-body font-bold">Keep Momentum Going</h3>
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
      </div>
    </div>
  );
}
