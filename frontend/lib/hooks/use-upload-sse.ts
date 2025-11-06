import { useEffect, useRef, useCallback } from 'react';
import { toast } from 'sonner';
import { logger } from '@/lib/utils/logger';
import { UploadState, AppAction } from '@/stores/app-store';

interface UseUploadSSEOptions {
  uploadState: UploadState;
  dispatch: React.Dispatch<AppAction>;
}

const PROGRESS_RESET_DELAY_MS = 4000;

function formatProgressDetails(details?: Record<string, unknown>): string | null {
  if (!details) {
    return null;
  }

  const formatEntry = (entry: any, fallbackLabel: string) => {
    if (!entry || typeof entry !== 'object') {
      return null;
    }
    const label =
      typeof entry.label === 'string' && entry.label.trim().length > 0
        ? entry.label
        : fallbackLabel;
    const current = Number((entry as any).current ?? 0);
    const total = Number((entry as any).total ?? 0);
    if (Number.isFinite(total) && total > 0) {
      return `${label} ${current}/${total}`;
    }
    return `${label} ${current}`;
  };

  const segments: string[] = [];
  const indexing = formatEntry(details.indexing, 'Indexing');
  if (indexing) {
    segments.push(indexing);
  }
  const ocr = formatEntry(details.ocr, 'DeepSeek OCR');
  if (ocr) {
    segments.push(ocr);
  }

  if (segments.length === 0) {
    for (const [key, value] of Object.entries(details)) {
      const fallback = key[0].toUpperCase() + key.slice(1);
      const segment = formatEntry(value as any, fallback);
      if (segment) {
        segments.push(segment);
      }
    }
  }

  return segments.length > 0 ? segments.join(' • ') : null;
}

/**
 * Hook to manage SSE connection for upload progress tracking
 */
export function useUploadSSE({ uploadState, dispatch }: UseUploadSSEOptions) {
  const eventSourceRef = useRef<EventSource | null>(null);
  const lastProgressTimeRef = useRef<number>(0);
  const stallCheckIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const resetProgressTimerRef = useRef<NodeJS.Timeout | null>(null);

  const clearProgressResetTimer = useCallback(() => {
    if (resetProgressTimerRef.current) {
      clearTimeout(resetProgressTimerRef.current);
      resetProgressTimerRef.current = null;
    }
  }, []);

  const scheduleProgressReset = useCallback(() => {
    clearProgressResetTimer();
    resetProgressTimerRef.current = setTimeout(() => {
      dispatch({ type: 'UPLOAD_SET_PROGRESS', payload: 0 });
      resetProgressTimerRef.current = null;
    }, PROGRESS_RESET_DELAY_MS);
  }, [clearProgressResetTimer, dispatch]);

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

    clearProgressResetTimer();

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
        const detailMessage = formatProgressDetails(data.details as Record<string, unknown> | undefined);
        const statusMessage =
          typeof data.message === 'string' && data.message.trim().length > 0
            ? data.message
            : detailMessage;
        dispatch({ type: 'UPLOAD_SET_STATUS_TEXT', payload: statusMessage ?? null });

        if (data.status === 'completed') {
          closeSSEConnection();
          dispatch({ type: 'UPLOAD_SET_PROGRESS', payload: 100 });
          const successMsg = data.message || `Upload completed`;
          dispatch({ type: 'UPLOAD_SET_MESSAGE', payload: successMsg });
          dispatch({ type: 'UPLOAD_SET_STATUS_TEXT', payload: null });
          dispatch({ type: 'UPLOAD_SET_UPLOADING', payload: false });
          dispatch({ type: 'UPLOAD_SET_JOB_ID', payload: null });
          dispatch({ type: 'UPLOAD_SET_FILES', payload: null }); // Clear files on completion
          dispatch({ type: 'UPLOAD_SET_FILE_META', payload: null });
          scheduleProgressReset();

          // Show toast notification
          if (typeof window !== 'undefined') {
            window.dispatchEvent(new Event('systemStatusChanged'));
            toast.success('Upload Complete', { description: successMsg });
          }

        } else if (data.status === 'failed') {
          closeSSEConnection();
          const errMsg = data.error || 'Upload failed';
          dispatch({ type: 'UPLOAD_SET_ERROR', payload: errMsg });
          dispatch({ type: 'UPLOAD_SET_STATUS_TEXT', payload: null });
          dispatch({ type: 'UPLOAD_SET_UPLOADING', payload: false });
          dispatch({ type: 'UPLOAD_SET_JOB_ID', payload: null });
          dispatch({ type: 'UPLOAD_SET_FILE_META', payload: null });
          scheduleProgressReset();

          // Show toast notification
          if (typeof window !== 'undefined') {
            toast.error('Upload Failed', { description: errMsg });
          }
        } else if (data.status === 'cancelled') {
          closeSSEConnection();
          const cancelMsg = data.message || 'Upload cancelled';
          dispatch({ type: 'UPLOAD_SET_MESSAGE', payload: cancelMsg });
          dispatch({ type: 'UPLOAD_SET_STATUS_TEXT', payload: null });
          dispatch({ type: 'UPLOAD_SET_UPLOADING', payload: false });
          dispatch({ type: 'UPLOAD_SET_JOB_ID', payload: null });
          dispatch({ type: 'UPLOAD_SET_FILES', payload: null });
          dispatch({ type: 'UPLOAD_SET_FILE_META', payload: null });
          scheduleProgressReset();

          // Show toast notification
          if (typeof window !== 'undefined') {
            toast.info('Upload Status', { description: cancelMsg });
          }
        }
      } catch (e) {
        logger.warn('Failed to parse SSE data', { error: e });
      }
    });

    // Handle heartbeat events to prevent stall detection
    es.addEventListener('heartbeat', () => {
      lastProgressTimeRef.current = Date.now(); // Update last activity time
    });

    es.addEventListener('not_found', () => {
      closeSSEConnection();
      dispatch({ type: 'UPLOAD_SET_ERROR', payload: 'Upload job not found. It may have completed or failed.' });
      dispatch({ type: 'UPLOAD_SET_UPLOADING', payload: false });
      dispatch({ type: 'UPLOAD_SET_JOB_ID', payload: null });
      dispatch({ type: 'UPLOAD_SET_STATUS_TEXT', payload: null });
      dispatch({ type: 'UPLOAD_SET_FILE_META', payload: null });
      dispatch({ type: 'UPLOAD_SET_PROGRESS', payload: 0 });
      scheduleProgressReset();
    });

    es.addEventListener('error', (e) => {
      logger.warn('Global SSE connection error', { error: e, jobId: uploadState.jobId });
      // Check if connection is permanently failed (readyState === 2 means CLOSED)
      if (es.readyState === 2) {
        logger.error('SSE connection permanently closed', { readyState: es.readyState });
        setTimeout(() => {
          // Check if still uploading after a brief delay
          if (uploadState.uploading && uploadState.jobId) {
            closeSSEConnection();
            dispatch({ type: 'UPLOAD_SET_ERROR', payload: 'Connection lost. The collection may have been deleted or the service is unavailable.' });
            dispatch({ type: 'UPLOAD_SET_STATUS_TEXT', payload: null });
            dispatch({ type: 'UPLOAD_SET_UPLOADING', payload: false });
            dispatch({ type: 'UPLOAD_SET_JOB_ID', payload: null });
            dispatch({ type: 'UPLOAD_SET_FILE_META', payload: null });
            scheduleProgressReset();

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
        logger.error('Upload stalled - no progress for 45 seconds', {
          timeSinceLastProgress,
          jobId: uploadState.jobId
        });
        closeSSEConnection();
        dispatch({ type: 'UPLOAD_SET_ERROR', payload: 'Upload stalled. The collection may have been deleted or the service is unavailable.' });
        dispatch({ type: 'UPLOAD_SET_STATUS_TEXT', payload: null });
        dispatch({ type: 'UPLOAD_SET_UPLOADING', payload: false });
        dispatch({ type: 'UPLOAD_SET_JOB_ID', payload: null });
        dispatch({ type: 'UPLOAD_SET_FILE_META', payload: null });
        scheduleProgressReset();

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
  }, [uploadState.jobId, uploadState.uploading, clearProgressResetTimer, closeSSEConnection, dispatch, scheduleProgressReset]);

  // Cleanup SSE connection on unmount
  useEffect(() => {
    return () => {
      closeSSEConnection();
      clearProgressResetTimer();
    };
  }, [clearProgressResetTimer, closeSSEConnection]);

  return { closeSSEConnection };
}
