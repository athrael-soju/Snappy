"use client";

import { useRef, useEffect, useCallback, useState } from "react";
import { MaintenanceService } from "@/lib/api/generated";
import "@/lib/api/client";
import { CloudUpload } from "lucide-react";
import { motion } from "framer-motion";
import { useSystemStatus } from "@/stores/app-store";
import { useFileUpload } from "@/lib/hooks/use-file-upload";
import { PageHeader } from "@/components/page-header";
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
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="page-shell page-section flex flex-col min-h-0 flex-1 space-y-6"
    >
      <PageHeader
        title="Upload Documents"
        description="Drag & drop or select files to add to your visual search index"
        icon={CloudUpload}
      />

      <div className="flex-1 min-h-0 flex flex-col overflow-hidden">
        <div className="space-y-6 pb-6">
          <SystemStatusWarning isReady={isReady} />

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

          <UploadInfoCards />
        </div>
      </div>
    </motion.div>
  );
}
