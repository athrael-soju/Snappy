"use client";

import { useRef, useEffect, useCallback, useState } from "react";
import { MaintenanceService } from "@/lib/api/generated";
import "@/lib/api/client";
import { useSystemStatus } from "@/stores/app-store";
import { useFileUpload } from "@/lib/hooks/use-file-upload";
import { AppPage } from "@/components/layout";
import {
  FileDropzone,
  SystemStatusWarning,
  UploadInfoCards
} from "@/components/upload";

export default function UploadPage() {
  const { systemStatus, setStatus, isReady: systemReady } = useSystemStatus();
  const [statusLoading, setStatusLoading] = useState(false);
  const hasFetchedRef = useRef(false);

  const isReady = !!systemReady;

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

  // Fetch system status function
  const fetchSystemStatus = useCallback(async () => {
    setStatusLoading(true);
    try {
      const status = await MaintenanceService.getStatusStatusGet();
      setStatus({ ...status, lastChecked: Date.now() });
      hasFetchedRef.current = true;
    } catch (err) {
      console.error('Failed to fetch system status:', err);
    } finally {
      setStatusLoading(false);
    }
  }, [setStatus]);

  // Fetch system status on mount and listen for changes
  useEffect(() => {
    if (!hasFetchedRef.current) {
      fetchSystemStatus();
    }

    window.addEventListener('systemStatusChanged', fetchSystemStatus);

    return () => {
      window.removeEventListener('systemStatusChanged', fetchSystemStatus);
    };
  }, [fetchSystemStatus]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await handleUpload(isReady);
  };

  return (
    <AppPage
      title="Upload"
      description="Add new documents to the visual search index with drag-and-drop or direct selection."
      contentClassName="stack stack-lg"
    >
      <SystemStatusWarning isReady={isReady} />

      <div className="stack stack-lg">
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
        {!hasFiles ? <UploadInfoCards /> : null}
      </div>
    </AppPage>
  );
}
