import { useState, useRef, useCallback, useEffect } from "react";
import { useUploadStore } from "@/stores/app-store";
import { ApiError } from "@/lib/api/generated";
import { toast } from "sonner";

const SUCCESS_MESSAGE_DISMISS_MS = 4500;
const ERROR_MESSAGE_DISMISS_MS = 6000;

const toFileArray = (input: FileList | File[] | null): File[] | null => {
  if (!input) {
    return null;
  }
  const filesArray = Array.from(input as ArrayLike<File>);
  return filesArray.length > 0 ? filesArray : null;
};

export function useFileUpload() {
  const {
    files,
    fileMeta,
    uploading,
    uploadProgress,
    message,
    error,
    jobId,
    statusText,
    setFiles,
    setUploading,
    setProgress,
    setMessage,
    setError,
    setJobId,
    setStatusText,
    cancelUpload,
  } = useUploadStore();

  const [isDragOver, setIsDragOver] = useState(false);
  const isCancellingRef = useRef(false);

  // Clear success/error messages after some time
  useEffect(() => {
    if (message && !uploading) {
      const timer = setTimeout(() => {
        setMessage(null);
      }, SUCCESS_MESSAGE_DISMISS_MS);
      return () => clearTimeout(timer);
    }
  }, [message, uploading, setMessage]);

  useEffect(() => {
    if (error && !uploading) {
      const timer = setTimeout(() => {
        setError(null);
      }, ERROR_MESSAGE_DISMISS_MS);
      return () => clearTimeout(timer);
    }
  }, [error, uploading, setError]);

  // Reset cancelling flag after cancellation completes
  useEffect(() => {
    if (!uploading && isCancellingRef.current) {
      const timer = setTimeout(() => {
        isCancellingRef.current = false;
      }, 500);
      return () => clearTimeout(timer);
    }
  }, [uploading]);

  // Drag and drop handlers
  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    const droppedFiles = toFileArray(e.dataTransfer.files);
    if (droppedFiles && droppedFiles.length > 0) {
      setFiles(droppedFiles);
    }
  }, [setFiles]);

  const handleFileSelect = useCallback((selectedFiles: FileList | File[] | null) => {
    const nextFiles = toFileArray(selectedFiles);
    if (nextFiles) {
      setFiles(nextFiles);
    } else {
      setFiles(null);
    }
  }, [setFiles]);

  const handleUpload = useCallback(async (isReady: boolean) => {
    // Prevent re-submission while already uploading or cancelling
    if (uploading || isCancellingRef.current) {
      console.warn('Upload already in progress or cancelling, ignoring submission');
      return;
    }
    
    if (!files || files.length === 0) return;
    
    // Check if system is ready
    if (!isReady) {
      toast.error('System Not Ready', { 
        description: 'Initialize collection and bucket before uploading' 
      });
      return;
    }
    
    isCancellingRef.current = false;
    setUploading(true);
    setProgress(0);
    setMessage(null);
    setError(null);
    setStatusText(null);
    setJobId(null);
    
    try {
      const formData = new FormData();
      files.forEach((f) => formData.append("files", f));

      const startRes = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL || ''}/index`, {
        method: "POST",
        body: formData,
      });
      
      if (!startRes.ok) {
        const t = await startRes.text();
        throw new Error(`Failed to start indexing: ${startRes.status} ${t}`);
      }
      
      const startData = await startRes.json();
      const startedJobId: string = startData.job_id;
      const total: number = Number(startData.total ?? 0);
      setJobId(startedJobId);
      setStatusText(total > 0 ? `Queued ${total} pages` : 'Preparing documents...');
      
    } catch (err: unknown) {
      setProgress(0);
      
      let errorMsg = "Upload failed";
      if (err instanceof ApiError) {
        errorMsg = `${err.status}: ${err.message}`;
      } else if (err instanceof Error) {
        errorMsg = err.message;
      }
      setError(errorMsg);
      toast.error("Upload Failed", { 
        description: errorMsg 
      });
      setUploading(false);
    }
  }, [files, uploading, setUploading, setProgress, setMessage, setError, setJobId, setStatusText]);

  const handleCancel = useCallback(() => {
    isCancellingRef.current = true;
    cancelUpload();
  }, [cancelUpload]);

  const handleClear = useCallback(() => {
    setFiles(null);
    setMessage(null);
    setError(null);
  }, [setFiles, setMessage, setError]);

  return {
    // State
    files,
    fileMeta,
    uploading,
    uploadProgress,
    message,
    error,
    jobId,
    statusText,
    isDragOver,
    isCancelling: isCancellingRef.current,
    
    // Computed
    fileCount: files && files.length > 0
      ? files.length
      : fileMeta && fileMeta.length > 0
        ? fileMeta.length
        : 0,
    hasFiles:
      (files && files.length > 0) ||
      (uploading && fileMeta && fileMeta.length > 0),
    
    // Handlers
    handleDragOver,
    handleDragLeave,
    handleDrop,
    handleFileSelect,
    handleUpload,
    handleCancel,
    handleClear,
  };
}

