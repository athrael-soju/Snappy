import { useAppStore } from '@/stores/app-store';
import { toast } from 'sonner';

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
    
    // First, clear jobId to stop SSE connection (it watches jobId)
    // This will trigger the SSE cleanup before we change other state
    dispatch({ type: 'UPLOAD_SET_JOB_ID', payload: null });
    
    // Then reset other upload state
    dispatch({ type: 'UPLOAD_SET_UPLOADING', payload: false });
    dispatch({ type: 'UPLOAD_SET_PROGRESS', payload: 0 });
    dispatch({ type: 'UPLOAD_SET_STATUS_TEXT', payload: null });
    
    try {
      // Call backend to cancel (best effort)
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL || ''}/index/cancel/${jobId}`, {
        method: 'POST',
      });
      
      if (response.ok) {
        dispatch({ type: 'UPLOAD_SET_ERROR', payload: null });
        dispatch({ type: 'UPLOAD_SET_MESSAGE', payload: 'Upload cancelled' });
        
        if (typeof window !== 'undefined') {
          toast.success('Upload Cancelled', { 
            description: 'The upload has been stopped successfully' 
          });
        }
      } else {
        console.warn(`Backend cancel failed: ${response.statusText}`);
        dispatch({ type: 'UPLOAD_SET_ERROR', payload: 'Cancellation may not have completed on server' });
        dispatch({ type: 'UPLOAD_SET_MESSAGE', payload: null });
        
        if (typeof window !== 'undefined') {
          toast.warning('Upload Stopped', { 
            description: 'Upload stopped locally, but server may still be processing' 
          });
        }
      }      
    } catch (error) {
      console.error('Failed to cancel upload on backend:', error);
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
    setFiles: (files: FileList | null) => 
      dispatch({ type: 'UPLOAD_SET_FILES', payload: files }),
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
    reset: () => dispatch({ type: 'UPLOAD_RESET' }),
    cancelUpload,
  };
}
