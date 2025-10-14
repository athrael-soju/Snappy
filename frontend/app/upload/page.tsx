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
    <div className="mx-auto flex w-full max-w-5xl flex-1 flex-col gap-6 px-4 py-8 sm:px-6 lg:px-8">
      <PageHeader
        title="Upload documents"
        description="Drop PDFs or images, watch Snappy extract pages, and keep track of progress in real time."
        icon={CloudUpload}
      />

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

      {!hasFiles && <UploadInfoCards />}
    </div>
  );
}
