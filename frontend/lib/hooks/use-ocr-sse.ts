import { useEffect, useRef, useCallback } from 'react';
import { toast } from 'sonner';
import { UploadState, AppAction } from '@/stores/app-store';

interface UseOcrSSEOptions {
  uploadState: UploadState;
  dispatch: React.Dispatch<AppAction>;
}

/**
 * Hook to manage SSE connection for OCR progress tracking
 * Monitors OCR job progress separately from upload/indexing
 */
export function useOcrSSE({ uploadState, dispatch }: UseOcrSSEOptions) {
  const eventSourceRef = useRef<EventSource | null>(null);
  const lastProgressTimeRef = useRef<number>(0);
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

  // OCR SSE connection management
  useEffect(() => {
    // Only connect if we have a valid OCR job ID
    if (!uploadState.ocrJobId) {
      closeSSEConnection();
      return;
    }

    // Don't create multiple connections
    if (eventSourceRef.current) {
      return;
    }

    // Reset last progress time when starting new connection
    lastProgressTimeRef.current = Date.now();

    const es = new EventSource(
      `${process.env.NEXT_PUBLIC_API_BASE_URL || ''}/ocr/progress/stream/${uploadState.ocrJobId}`
    );
    eventSourceRef.current = es;

    es.addEventListener('progress', (ev: MessageEvent) => {
      try {
        const data = JSON.parse(ev.data || '{}');
        const pct = Number(data.percent ?? 0);
        lastProgressTimeRef.current = Date.now();

        dispatch({ type: 'UPLOAD_SET_OCR_PROGRESS', payload: pct });

        const statusMessage =
          typeof data.message === 'string' && data.message.trim().length > 0
            ? data.message
            : null;
        dispatch({ type: 'UPLOAD_SET_OCR_STATUS_TEXT', payload: statusMessage });

        if (data.status === 'completed') {
          closeSSEConnection();
          dispatch({ type: 'UPLOAD_SET_OCR_PROGRESS', payload: 100 });
          const successMsg = data.message || 'OCR processing completed';
          dispatch({ type: 'UPLOAD_SET_OCR_STATUS_TEXT', payload: successMsg });
          dispatch({ type: 'UPLOAD_SET_OCR_JOB_ID', payload: null });

          // Show toast notification
          if (typeof window !== 'undefined') {
            window.dispatchEvent(new Event('systemStatusChanged'));
            toast.success('OCR Complete', { description: successMsg });
          }
        } else if (data.status === 'failed') {
          closeSSEConnection();
          const errMsg = data.error || 'OCR processing failed';
          dispatch({ type: 'UPLOAD_SET_OCR_ERROR', payload: errMsg });
          dispatch({ type: 'UPLOAD_SET_OCR_STATUS_TEXT', payload: null });
          dispatch({ type: 'UPLOAD_SET_OCR_JOB_ID', payload: null });

          // Show toast notification
          if (typeof window !== 'undefined') {
            toast.error('OCR Failed', { description: errMsg });
          }
        } else if (data.status === 'cancelled') {
          closeSSEConnection();
          const cancelMsg = data.message || 'OCR processing cancelled';
          dispatch({ type: 'UPLOAD_SET_OCR_STATUS_TEXT', payload: cancelMsg });
          dispatch({ type: 'UPLOAD_SET_OCR_JOB_ID', payload: null });

          // Show toast notification
          if (typeof window !== 'undefined') {
            toast.info('OCR Status', { description: cancelMsg });
          }
        }
      } catch (e) {
        console.warn('Failed to parse OCR SSE data:', e);
      }
    });

    // Handle heartbeat events to prevent stall detection
    es.addEventListener('heartbeat', () => {
      lastProgressTimeRef.current = Date.now();
    });

    es.addEventListener('not_found', () => {
      closeSSEConnection();
      dispatch({
        type: 'UPLOAD_SET_OCR_ERROR',
        payload: 'OCR job not found. It may have completed or failed.',
      });
      dispatch({ type: 'UPLOAD_SET_OCR_JOB_ID', payload: null });
      dispatch({ type: 'UPLOAD_SET_OCR_STATUS_TEXT', payload: null });
    });

    es.addEventListener('error', (e) => {
      console.warn('OCR SSE connection error:', e);
      // Check if connection is permanently failed (readyState === 2 means CLOSED)
      if (es.readyState === 2) {
        console.error('OCR SSE connection permanently closed');
        setTimeout(() => {
          if (uploadState.ocrJobId) {
            closeSSEConnection();
            dispatch({
              type: 'UPLOAD_SET_OCR_ERROR',
              payload: 'Connection lost during OCR processing.',
            });
            dispatch({ type: 'UPLOAD_SET_OCR_STATUS_TEXT', payload: null });
            dispatch({ type: 'UPLOAD_SET_OCR_JOB_ID', payload: null });

            if (typeof window !== 'undefined') {
              toast.error('OCR Failed', {
                description: 'Connection lost during OCR processing.',
              });
            }
          }
        }, 2000);
      }
    });

    // Monitor for stalled OCR processing (no progress for 60 seconds)
    stallCheckIntervalRef.current = setInterval(() => {
      const timeSinceLastProgress = Date.now() - lastProgressTimeRef.current;
      if (timeSinceLastProgress > 60000) {
        // 60 seconds without progress
        console.error('OCR processing stalled - no progress for 60 seconds');
        closeSSEConnection();
        dispatch({
          type: 'UPLOAD_SET_OCR_ERROR',
          payload: 'OCR processing stalled or service unavailable.',
        });
        dispatch({ type: 'UPLOAD_SET_OCR_STATUS_TEXT', payload: null });
        dispatch({ type: 'UPLOAD_SET_OCR_JOB_ID', payload: null });

        if (typeof window !== 'undefined') {
          toast.error('OCR Failed', {
            description: 'OCR processing stalled or service unavailable.',
          });
        }
      }
    }, 15000); // Check every 15 seconds

    return () => {
      closeSSEConnection();
    };
  }, [uploadState.ocrJobId, closeSSEConnection, dispatch]);

  // Cleanup SSE connection on unmount
  useEffect(() => {
    return () => {
      closeSSEConnection();
    };
  }, [closeSSEConnection]);

  return { closeSSEConnection };
}
