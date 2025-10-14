"use client";

import { useRef, useEffect, useCallback, useState } from "react";
import { MaintenanceService } from "@/lib/api/generated";
import "@/lib/api/client";
import { CloudUpload } from "lucide-react";
import { motion } from "framer-motion";
import { defaultPageMotion, sectionVariants } from "@/lib/motion-presets";
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
    <motion.div {...defaultPageMotion}
      className="page-shell flex flex-col gap-4 h-screen overflow-hidden py-4"
    >
      <motion.section variants={sectionVariants} className="flex-shrink-0">
        <PageHeader
          title="Upload Documents"
          icon={CloudUpload}
          tooltip="Drag & drop or select files to add to your visual search index"
        />
      </motion.section>

      <motion.section variants={sectionVariants} className="flex-1 overflow-y-auto min-h-0">
        <div className="mx-auto w-full max-w-5xl flex flex-col gap-6 pb-4">
            {/* System Status Warning */}
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
          {!hasFiles && <UploadInfoCards />}
        </div>
      </motion.section>
    </motion.div>
  );
}


