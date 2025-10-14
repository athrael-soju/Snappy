"use client";

import { useRef, useEffect, useCallback, useState } from "react";
import { CloudUpload } from "lucide-react";

import { MaintenanceService } from "@/lib/api/generated";
import "@/lib/api/client";
import { useSystemStatus } from "@/stores/app-store";
import { useFileUpload } from "@/lib/hooks/use-file-upload";
import { PageHeader } from "@/components/page-header";
import { FileDropzone, SystemStatusWarning, UploadInfoCards } from "@/components/upload";

export default function UploadPage() {
  const { setStatus, isReady: systemReady } = useSystemStatus();
  const [statusLoading, setStatusLoading] = useState(false);
  const hasFetchedRef = useRef(false);
  const isReady = Boolean(systemReady);

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
  } = useFileUpload();

  const fetchSystemStatus = useCallback(async () => {
    setStatusLoading(true);
    try {
      const status = await MaintenanceService.getStatusStatusGet();
      setStatus({ ...status, lastChecked: Date.now() });
      hasFetchedRef.current = true;
    } catch (err) {
      console.error("Failed to fetch system status", err);
    } finally {
      setStatusLoading(false);
    }
  }, [setStatus]);

  useEffect(() => {
    if (!hasFetchedRef.current) {
      fetchSystemStatus();
    }
    window.addEventListener("systemStatusChanged", fetchSystemStatus);
    return () => window.removeEventListener("systemStatusChanged", fetchSystemStatus);
  }, [fetchSystemStatus]);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    await handleUpload(isReady);
  };

  return (
    <div className="flex min-h-screen flex-col">
      {/* Header Section */}
      <div className="border-b bg-gradient-to-br from-blue-500/5 to-background px-6 py-12 sm:px-8 lg:px-12">
        <div className="mx-auto max-w-7xl">
          <div className="space-y-4">
            <div className="flex items-center gap-3">
              <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-blue-500/10">
                <CloudUpload className="h-6 w-6 text-blue-600 dark:text-blue-400" />
              </div>
              <div>
                <h1 className="text-3xl font-bold tracking-tight text-foreground sm:text-4xl">
                  Upload Documents
                </h1>
                <p className="text-sm text-muted-foreground sm:text-base">
                  Drop PDFs or images and watch real-time processing
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="mx-auto w-full max-w-7xl flex-1 px-6 py-8 sm:px-8 lg:px-12">
        <div className="grid gap-6 lg:grid-cols-[1fr_350px]">
          {/* Main Content */}
          <div className="space-y-6">
            <SystemStatusWarning isReady={isReady} isLoading={statusLoading} className="rounded-2xl" />

            <FileDropzone
              isDragOver={isDragOver}
              uploading={uploading}
              files={files}
              fileCount={fileCount}
              hasFiles={hasFiles}
              uploadProgress={uploadProgress}
              statusText={statusText}
              jobId={jobId}
              message={message}
              error={error}
              isReady={isReady}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              onFileSelect={handleFileSelect}
              onSubmit={handleSubmit}
              onCancel={handleCancel}
            />
          </div>

          {/* Sidebar */}
          {!hasFiles && (
            <div className="lg:sticky lg:top-6 lg:h-fit">
              <UploadInfoCards />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
