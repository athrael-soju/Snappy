"use client";

import { FormEvent } from "react";
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
        <div className="mx-auto flex h-full w-full max-w-5xl flex-col space-y-4">
          {/* Header Section */}
          <div className="shrink-0 space-y-2 text-center">
            <h1 className="text-2xl font-bold tracking-tight sm:text-3xl lg:text-4xl">
              <span className="bg-gradient-to-br from-foreground via-foreground to-foreground/70 bg-clip-text text-transparent">
                Upload & Index
              </span>
              {" "}
              <span className="bg-gradient-to-r from-blue-500 via-cyan-500 to-blue-500 bg-clip-text text-transparent">
                Your Documents
              </span>
            </h1>
            
            <p className="mx-auto max-w-2xl text-xs leading-relaxed text-muted-foreground sm:text-sm">
              Drop your documents and let ColPali&apos;s vision AI understand both text and layout.
            </p>
          </div>

          {/* Compact System Status */}
          <div className="flex shrink-0 flex-wrap items-center justify-center gap-2 text-xs">
            <Badge 
              variant={isReady ? "default" : "destructive"}
              className="gap-1.5 px-3 py-1"
            >
              {isReady ? (
                <>
                  <CheckCircle2 className="h-3 w-3" />
                  Ready
                </>
              ) : (
                <>
                  <AlertCircle className="h-3 w-3" />
                  Not Ready
                </>
              )}
            </Badge>
            
            <Badge variant="outline" className="gap-1.5 px-3 py-1">
              <Database className="h-3 w-3" />
              {systemStatus?.collection?.name ?? "unknown"}
              {systemStatus?.collection?.exists ? (
                <CheckCircle2 className="h-3 w-3 text-green-500" />
              ) : (
                <AlertCircle className="h-3 w-3 text-red-500" />
              )}
              {typeof systemStatus?.collection?.vector_count === "number" && (
                <span className="ml-1 font-semibold">
                  ({systemStatus.collection.vector_count.toLocaleString()})
                </span>
              )}
            </Badge>
            
            <Badge variant="outline" className="gap-1.5 px-3 py-1">
              <HardDrive className="h-3 w-3" />
              {systemStatus?.bucket?.name ?? "unknown"}
              {systemStatus?.bucket?.exists && !systemStatus?.bucket?.disabled ? (
                <CheckCircle2 className="h-3 w-3 text-green-500" />
              ) : (
                <AlertCircle className="h-3 w-3 text-red-500" />
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
              className="h-6 gap-1.5 rounded-full px-3 text-xs"
            >
              {statusLoading ? (
                <Loader2 className="h-3 w-3 animate-spin" />
              ) : (
                <RefreshCw className="h-3 w-3" />
              )}
              Refresh
            </Button>
          </div>

          {/* Upload Form */}
          <form onSubmit={handleSubmit} className="flex min-h-0 flex-1 flex-col space-y-4">
            {/* Drag & Drop Zone */}
            <div
              className={`group relative overflow-hidden rounded-2xl border-2 border-dashed transition-all ${
                isDragOver
                  ? "border-primary bg-primary/5 shadow-xl shadow-primary/25"
                  : "border-border/50 bg-card/30 backdrop-blur-sm hover:border-primary/50"
              }`}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
            >
              <div className={`absolute inset-0 bg-gradient-to-br from-blue-500 to-cyan-500 opacity-0 transition-opacity ${isDragOver ? "opacity-10" : "group-hover:opacity-5"}`} />
              
              <div className="relative flex min-h-[180px] flex-col items-center justify-center gap-3 p-6">
                <div className="flex h-14 w-14 items-center justify-center rounded-xl bg-gradient-to-br from-blue-500 to-cyan-500 shadow-lg">
                  <Upload className="h-7 w-7 text-primary-foreground" />
                </div>
                
                <div className="text-center space-y-1">
                  <h3 className="text-base font-bold">
                    {isDragOver ? "Drop files here" : "Drag & drop your files"}
                  </h3>
                  <p className="text-xs text-muted-foreground">
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
                      className="gap-2 rounded-full border-2 bg-background/50 px-4 backdrop-blur-sm cursor-pointer"
                      onClick={() => document.getElementById('file-input')?.click()}
                    >
                      <FileText className="h-4 w-4" />
                      Browse
                    </Button>
                  </label>
                  
                  {hasFiles && (
                    <>
                      <Button
                        type="submit"
                        size="sm"
                        disabled={!hasFiles || uploading || !isReady}
                        className="group gap-2 rounded-full px-4 shadow-lg shadow-primary/20"
                      >
                        {uploading ? (
                          <>
                            <Loader2 className="h-4 w-4 animate-spin" />
                            <span className="hidden sm:inline">Uploading...</span>
                          </>
                        ) : (
                          <>
                            <Upload className="h-4 w-4" />
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
                          className="gap-2 rounded-full px-3"
                        >
                          <X className="h-4 w-4" />
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
            </div>

            {/* Selected Files */}
            {hasFiles && (
              <div className="flex min-h-0 flex-1 flex-col rounded-xl border border-border/50 bg-card/50 p-3 backdrop-blur-sm">
                <div className="mb-2 flex shrink-0 items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <Sparkles className="h-4 w-4 text-primary" />
                    <h3 className="text-sm font-bold">
                      Ready to Upload ({fileCount} {fileCount === 1 ? "file" : "files"})
                    </h3>
                  </div>
                  <Button
                    type="button"
                    onClick={handleClear}
                    size="sm"
                    variant="ghost"
                    disabled={uploading}
                    className="h-7 gap-1.5 rounded-full px-2 text-xs"
                  >
                    <X className="h-3 w-3" />
                    Clear
                  </Button>
                </div>
                
                <ScrollArea className="min-h-0 flex-1">
                  <div className="space-y-1.5 pr-4">
                  {selectedFiles.map((file, index) => (
                    <div 
                      key={file.name}
                      className="flex items-center justify-between rounded-lg border border-border/50 bg-background/50 px-3 py-2 transition-colors hover:bg-muted/50"
                    >
                      <div className="flex items-center gap-2 min-w-0">
                        <FileText className="h-4 w-4 shrink-0 text-primary" />
                        <div className="min-w-0">
                          <p className="truncate text-xs font-medium">{file.name}</p>
                          <p className="text-xs text-muted-foreground">
                            {(file.size / 1024).toFixed(1)} KB
                          </p>
                        </div>
                      </div>
                      {uploading && typeof uploadProgress === "number" && (
                        <div className="shrink-0 text-xs font-semibold text-primary">
                          {Math.round(uploadProgress)}%
                        </div>
                      )}
                    </div>
                  ))}
                  </div>
                </ScrollArea>
              </div>
            )}

            {/* Progress & Status Messages */}
            {(uploadProgress || statusText || jobId || message || error) && (
              <div className="space-y-2 rounded-xl border border-border/50 bg-card/50 p-4 backdrop-blur-sm">
                {typeof uploadProgress === "number" && uploadProgress > 0 && (
                  <div className="space-y-1.5">
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-medium">Upload Progress</span>
                      <span className="font-semibold text-primary">{Math.round(uploadProgress)}%</span>
                    </div>
                    <div className="h-2 overflow-hidden rounded-full bg-muted">
                      <div 
                        className="h-full bg-gradient-to-r from-blue-500 to-cyan-500 transition-all duration-300"
                        style={{ width: `${uploadProgress}%` }}
                      />
                    </div>
                  </div>
                )}
                
                {statusText && (
                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    {isStatusLoading ? (
                      <Loader2 className="h-3 w-3 animate-spin" />
                    ) : error ? (
                      <AlertCircle className="h-3 w-3 text-destructive" />
                    ) : (
                      <CheckCircle2 className="h-3 w-3 text-green-500" />
                    )}
                    {statusText}
                  </div>
                )}
                
                {jobId && (
                  <div className="rounded-lg bg-muted/50 px-2 py-1.5">
                    <p className="text-xs text-muted-foreground">
                      Job ID: <span className="font-mono">{jobId}</span>
                    </p>
                  </div>
                )}
                
                {message && (
                  <div className="flex items-center gap-2 rounded-lg bg-green-500/10 px-3 py-2 text-xs font-medium text-green-600 dark:text-green-400">
                    <CheckCircle2 className="h-4 w-4" />
                    {message}
                  </div>
                )}
                
                {error && (
                  <div className="flex items-center gap-2 rounded-lg bg-red-500/10 px-3 py-2 text-xs font-medium text-red-600 dark:text-red-400">
                    <AlertCircle className="h-4 w-4" />
                    {error}
                  </div>
                )}
              </div>
            )}

          </form>
        </div>
      </div>
    </div>
  );
}
