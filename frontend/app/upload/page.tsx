"use client";

import { FormEvent } from "react";
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
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import "@/lib/api/client";
import { useSystemStatus } from "@/stores/app-store";
import { useFileUpload } from "@/lib/hooks/use-file-upload";

export default function UploadPage() {
  const { systemStatus, statusLoading, fetchStatus, isReady } = useSystemStatus();
  const {
    files,
    uploading,
    uploadProgress,
    message,
    error,
    jobId,
    statusText,
    isDragOver,
    fileCount,
    hasFiles,
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

  const selectedFiles = files ? Array.from(files) : [];
  const isStatusLoading = uploading && (typeof uploadProgress !== "number" || uploadProgress < 100);

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
            className="shrink-0 space-y-2 text-center"
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1, duration: 0.3 }}
          >
            <h1 className="text-xl font-bold tracking-tight sm:text-2xl lg:text-3xl">
              <span className="bg-gradient-to-br from-foreground via-foreground to-foreground/70 bg-clip-text text-transparent">
                Upload & Index
              </span>
              {" "}
              <span className="bg-gradient-to-r from-chart-1 via-chart-2 to-chart-1 bg-clip-text text-transparent">
                Your Documents
              </span>
            </h1>
            
            <p className="mx-auto max-w-2xl text-body-xs leading-relaxed text-muted-foreground">
              Drop your documents and let Snappy&apos;s ColPali vision AI understand both text and layout.
            </p>
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
              {systemStatus?.collection?.name ?? "unknown"}
              {systemStatus?.collection?.exists ? (
                <CheckCircle2 className="size-icon-3xs text-chart-2" />
              ) : (
                <AlertCircle className="size-icon-3xs text-destructive" />
              )}
              {typeof systemStatus?.collection?.vector_count === "number" && (
                <span className="ml-1 font-semibold">
                  ({systemStatus.collection.vector_count.toLocaleString()})
                </span>
              )}
            </Badge>
            
            <Badge variant="outline" className="gap-1.5 px-3 py-1">
              <HardDrive className="size-icon-3xs" />
              {systemStatus?.bucket?.name ?? "unknown"}
              {systemStatus?.bucket?.exists && !systemStatus?.bucket?.disabled ? (
                <CheckCircle2 className="size-icon-3xs text-chart-2" />
              ) : (
                <AlertCircle className="size-icon-3xs text-destructive" />
              )}
              {typeof systemStatus?.bucket?.object_count === "number" && (
                <span className="ml-1 font-semibold">
                  ({systemStatus.bucket.object_count.toLocaleString()})
                </span>
              )}
            </Badge>
            
            <Button
              onClick={fetchStatus}
              disabled={statusLoading}
              variant="ghost"
              size="sm"
              className="h-6 gap-1.5 rounded-full px-3 text-body-xs"
            >
              {statusLoading ? (
                <Loader2 className="size-icon-3xs animate-spin" />
              ) : (
                <RefreshCw className="size-icon-3xs" />
              )}
              Refresh
            </Button>
          </motion.div>

          {/* Upload Form */}
          <form onSubmit={handleSubmit} className="flex min-h-0 flex-1 flex-col space-y-4">
            {/* Drag & Drop Zone */}
            <motion.div
              className={`group relative overflow-hidden rounded-2xl border-2 border-dashed transition-all ${
                isDragOver
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
                  <p className="text-body-sm text-muted-foreground">
                    or browse • PDFs, images, and documents
                  </p>
                </div>
                
                <div className="flex items-center gap-2">
                  <label htmlFor="file-input">
                    <Button 
                      type="button"
                      variant="outline"
                      size="sm"
                      disabled={uploading}
                      className="h-10 gap-2 rounded-full border-2 bg-background/50 px-5 backdrop-blur-sm cursor-pointer touch-manipulation"
                      onClick={() => document.getElementById('file-input')?.click()}
                    >
                      <FileText className="size-icon-xs" />
                      Browse Files
                    </Button>
                  </label>
                  
                  {hasFiles && (
                    <>
                      <Button
                        type="submit"
                        size="sm"
                        disabled={!hasFiles || uploading || !isReady}
                        className="group h-10 gap-2 rounded-full px-5 shadow-lg shadow-primary/20 touch-manipulation"
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
                      </Button>
                      
                      {uploading && (
                        <Button
                          type="button"
                          onClick={handleCancel}
                          size="sm"
                          variant="ghost"
                          className="h-10 gap-2 rounded-full px-4 touch-manipulation"
                        >
                          <X className="size-icon-xs" />
                          <span className="hidden sm:inline">Cancel</span>
                        </Button>
                      )}
                    </>
                  )}
                </div>
                
                <input
                  id="file-input"
                  type="file"
                  multiple
                  onChange={(event) => handleFileSelect(event.target.files)}
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
                  <Button
                    type="button"
                    onClick={handleClear}
                    size="sm"
                    variant="ghost"
                    disabled={uploading}
                    className="h-7 gap-1.5 rounded-full px-2 text-body-xs"
                  >
                    <X className="size-icon-3xs" />
                    Clear
                  </Button>
                </div>
                
                <ScrollArea className="min-h-0 flex-1">
                  <div className="space-y-1.5 pr-4">
                  {selectedFiles.map((file, index) => (
                    <motion.div 
                      key={file.name}
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
                          <p className="text-body-xs text-muted-foreground">
                            {(file.size / 1024).toFixed(1)} KB
                          </p>
                        </div>
                      </div>
                      {uploading && typeof uploadProgress === "number" && (
                        <div className="shrink-0 text-body-xs font-semibold text-primary">
                          {Math.round(uploadProgress)}%
                        </div>
                      )}
                    </motion.div>
                  ))}
                  </div>
                </ScrollArea>
              </motion.div>
            )}
            </AnimatePresence>

            {/* Progress & Status Messages */}
            <AnimatePresence mode="wait">
              {(uploadProgress || statusText || jobId || message || error) && (
                <motion.div 
                  className="space-y-2 rounded-xl border border-border/50 bg-card/50 p-4 backdrop-blur-sm"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  transition={{ duration: 0.3 }}
                >
                {typeof uploadProgress === "number" && uploadProgress > 0 && (
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
                
                {statusText && (
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

          </form>
        </motion.div>
      </div>
    </div>
  );
}
