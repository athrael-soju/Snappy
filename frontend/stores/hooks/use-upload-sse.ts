import { useEffect, useRef, useCallback } from 'react';
import { toast } from '@/components/ui/sonner';
import { UploadState, AppAction } from '@/stores/app-store';

interface UseUploadSSEOptions {
  uploadState: UploadState;
  dispatch: React.Dispatch<AppAction>;
}

/**
 * Hook to manage SSE connection for upload progress tracking
 */
export function useUploadSSE({ uploadState, dispatch }: UseUploadSSEOptions) {
  const eventSourceRef = useRef<EventSource | null>(null);
  const lastProgressTimeRef = useRef<number>(Date.now());
  const stallCheckIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Function to properly close existing SSE connection
  const closeSSEConnection = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
    if (stallCheckIntervalRef.current) {
      clearInterval(stallCheckIntervalRef.current);
      stallCheckIntervalRef.current = null;
    }
  }, []);

  // Global SSE connection management for uploads
  useEffect(() => {
    // Only connect if we have an ongoing upload with a valid job ID
    if (!uploadState.jobId || !uploadState.uploading) {
      closeSSEConnection();
      return;
    }

    // Don't create multiple connections
    if (eventSourceRef.current) {
      return;
    }
   
    // Reset last progress time when starting new connection
    lastProgressTimeRef.current = Date.now();
    
    const es = new EventSource(`${process.env.NEXT_PUBLIC_API_BASE_URL || ''}/progress/stream/${uploadState.jobId}`);
    eventSourceRef.current = es;

    es.addEventListener('progress', (ev: MessageEvent) => {
      try {
        const data = JSON.parse(ev.data || '{}');
        const pct = Number(data.percent ?? 0);
        lastProgressTimeRef.current = Date.now(); // Update last progress time
        dispatch({ type: 'UPLOAD_SET_PROGRESS', payload: pct });
        if (data.message) {
          dispatch({ type: 'UPLOAD_SET_STATUS_TEXT', payload: data.message });
        }

        if (data.status === 'completed') {
          closeSSEConnection();
          dispatch({ type: 'UPLOAD_SET_PROGRESS', payload: 100 });
          const successMsg = data.message || `Upload completed`;
          dispatch({ type: 'UPLOAD_SET_MESSAGE', payload: successMsg });
          dispatch({ type: 'UPLOAD_SET_UPLOADING', payload: false });
          dispatch({ type: 'UPLOAD_SET_JOB_ID', payload: null });
          dispatch({ type: 'UPLOAD_SET_FILES', payload: null }); // Clear files on completion
          
          // Show toast notification
          if (typeof window !== 'undefined') {
            toast.success('Upload Complete', { description: successMsg });
          }
        } else if (data.status === 'failed') {
          closeSSEConnection();
          const errMsg = data.error || 'Upload failed';
          dispatch({ type: 'UPLOAD_SET_ERROR', payload: errMsg });
          dispatch({ type: 'UPLOAD_SET_UPLOADING', payload: false });
          dispatch({ type: 'UPLOAD_SET_JOB_ID', payload: null });
          
          // Show toast notification
          if (typeof window !== 'undefined') {
            toast.error('Upload Failed', { description: errMsg });
          }
        } else if (data.status === 'cancelled') {
          closeSSEConnection();
          const cancelMsg = data.message || 'Upload cancelled';
          dispatch({ type: 'UPLOAD_SET_MESSAGE', payload: cancelMsg });
          dispatch({ type: 'UPLOAD_SET_UPLOADING', payload: false });
          dispatch({ type: 'UPLOAD_SET_JOB_ID', payload: null });
          dispatch({ type: 'UPLOAD_SET_FILES', payload: null });
          
          // Show toast notification
          if (typeof window !== 'undefined') {
            toast.info('Upload Status', { description: cancelMsg });
          }
        }
      } catch (e) {
        console.warn('Failed to parse SSE data:', e);
      }
    });

    es.addEventListener('not_found', () => {
      closeSSEConnection();
      dispatch({ type: 'UPLOAD_SET_ERROR', payload: 'Upload job not found. It may have completed or failed.' });
      dispatch({ type: 'UPLOAD_SET_UPLOADING', payload: false });
      dispatch({ type: 'UPLOAD_SET_JOB_ID', payload: null });
      dispatch({ type: 'UPLOAD_SET_PROGRESS', payload: 0 });
    });

    es.addEventListener('error', (e) => {
      console.warn('Global SSE connection error:', e);
      // Check if connection is permanently failed (readyState === 2 means CLOSED)
      if (es.readyState === 2) {
        console.error('SSE connection permanently closed');
        setTimeout(() => {
          // Check if still uploading after a brief delay
          if (uploadState.uploading && uploadState.jobId) {
            closeSSEConnection();
            dispatch({ type: 'UPLOAD_SET_ERROR', payload: 'Connection lost. The collection may have been deleted or the service is unavailable.' });
            dispatch({ type: 'UPLOAD_SET_UPLOADING', payload: false });
            dispatch({ type: 'UPLOAD_SET_JOB_ID', payload: null });
            
            if (typeof window !== 'undefined') {
              toast.error('Upload Failed', { 
                description: 'Connection lost. The collection may have been deleted.' 
              });
            }
          }
        }, 2000);
      }
    });

    // Monitor for stalled uploads (no progress for 45 seconds)
    stallCheckIntervalRef.current = setInterval(() => {
      const timeSinceLastProgress = Date.now() - lastProgressTimeRef.current;
      if (timeSinceLastProgress > 45000) { // 45 seconds without progress
        console.error('Upload stalled - no progress for 45 seconds');
        closeSSEConnection();
        dispatch({ type: 'UPLOAD_SET_ERROR', payload: 'Upload stalled. The collection may have been deleted or the service is unavailable.' });
        dispatch({ type: 'UPLOAD_SET_UPLOADING', payload: false });
        dispatch({ type: 'UPLOAD_SET_JOB_ID', payload: null });
        
        if (typeof window !== 'undefined') {
          toast.error('Upload Failed', { 
            description: 'Upload stalled. The collection may have been deleted.' 
          });
        }
      }
    }, 10000); // Check every 10 seconds

    return () => {
      closeSSEConnection();
    };
  }, [uploadState.jobId, uploadState.uploading, closeSSEConnection, dispatch]);

  // Cleanup SSE connection on unmount
  useEffect(() => {
    return () => {
      closeSSEConnection();
    };
  }, [closeSSEConnection]);

  return { closeSSEConnection };
}
