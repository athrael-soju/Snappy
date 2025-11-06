import { useAppStore } from '@/stores/app-store';
import { toast } from 'sonner';
import { logger } from '@/lib/utils/logger';
import type { UploadFileMeta } from '@/stores/types';

const toFileMeta = (files: File[] | null): UploadFileMeta[] | null => {
  if (!files || files.length === 0) {
    return null;
  }
  return files.map((file) => ({
    name: file.name,
    size: file.size,
    type: file.type,
    lastModified: file.lastModified,
  }));
};

/**
 * Hook for accessing and managing upload state
 */
export function useUploadStore() {
  const { state, dispatch } = useAppStore();

  const cancelUpload = async () => {
    const jobId = state.upload.jobId;

    if (!jobId) {
      return;
    }
    dispatch({ type: 'UPLOAD_SET_STATUS_TEXT', payload: 'Cancelling upload…' });

    try {
      // Call backend to cancel (best effort)
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL || ''}/index/cancel/${jobId}`, {
        method: 'POST',
      });

      if (response.ok) {
        dispatch({ type: 'UPLOAD_SET_ERROR', payload: null });
      } else {
        logger.warn('Backend cancel failed', {
          statusText: response.statusText,
          jobId
        });
        dispatch({ type: 'UPLOAD_SET_ERROR', payload: 'Cancellation may not have completed on server' });
        dispatch({ type: 'UPLOAD_SET_MESSAGE', payload: null });

        if (typeof window !== 'undefined') {
          toast.warning('Upload Stopped', {
            description: 'Upload stopped locally, but server may still be processing'
          });
        }
      }
    } catch (error) {
      logger.error('Failed to cancel upload on backend', { error, jobId });
      dispatch({ type: 'UPLOAD_SET_ERROR', payload: 'Connection error during cancellation' });
      dispatch({ type: 'UPLOAD_SET_MESSAGE', payload: null });

      if (typeof window !== 'undefined') {
        toast.error('Cancellation Error', {
          description: 'Could not reach server to cancel. Upload stopped locally.'
        });
      }
    }
  };

  return {
    ...state.upload,
    setFiles: (files: File[] | null) => {
      dispatch({ type: 'UPLOAD_SET_FILES', payload: files });
      dispatch({ type: 'UPLOAD_SET_FILE_META', payload: toFileMeta(files) });
      // Store filenames for OCR processing
      const filenames = files ? files.map(f => f.name) : null;
      dispatch({ type: 'UPLOAD_SET_UPLOADED_FILENAMES', payload: filenames });
    },
    setUploading: (uploading: boolean) =>
      dispatch({ type: 'UPLOAD_SET_UPLOADING', payload: uploading }),
    setProgress: (progress: number) =>
      dispatch({ type: 'UPLOAD_SET_PROGRESS', payload: progress }),
    setMessage: (message: string | null) =>
      dispatch({ type: 'UPLOAD_SET_MESSAGE', payload: message }),
    setError: (error: string | null) =>
      dispatch({ type: 'UPLOAD_SET_ERROR', payload: error }),
    setJobId: (jobId: string | null) =>
      dispatch({ type: 'UPLOAD_SET_JOB_ID', payload: jobId }),
    setStatusText: (statusText: string | null) =>
      dispatch({ type: 'UPLOAD_SET_STATUS_TEXT', payload: statusText }),
    setFileMeta: (meta: UploadFileMeta[] | null) =>
      dispatch({ type: 'UPLOAD_SET_FILE_META', payload: meta }),
    setOcrError: (error: string | null) =>
      dispatch({ type: 'UPLOAD_SET_OCR_ERROR', payload: error }),
    setOcrStatusText: (statusText: string | null) =>
      dispatch({ type: 'UPLOAD_SET_OCR_STATUS_TEXT', payload: statusText }),
    reset: () => dispatch({ type: 'UPLOAD_RESET' }),
    cancelUpload,
  };
}
