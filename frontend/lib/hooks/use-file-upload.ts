import { useState, useRef, useCallback, useEffect, useMemo } from "react";
import { useUploadStore } from "@/stores/app-store";
import { ApiError, ConfigurationService } from "@/lib/api/generated";
import { toast } from "sonner";
import { loadConfigFromStorage } from "@/lib/config/config-store";
import { logger } from "@/lib/utils/logger";

const MB_IN_BYTES = 1024 * 1024;
const RUNTIME_CONFIG_EVENT = "runtimeConfigUpdated";
const RUNTIME_CONFIG_SYNCED_EVENT = "runtimeConfigSynced";

type UploadConstraints = {
  allowedTypes: string[];
  maxFiles: number;
  maxFileSizeMb: number;
};

type FileTypeMeta = {
  label: string;
  extensions: string[];
  mimeTypes: string[];
};

const FILE_TYPE_METADATA: Record<string, FileTypeMeta> = {
  pdf: {
    label: "PDF",
    extensions: [".pdf"],
    mimeTypes: ["application/pdf"],
  },
};

const DEFAULT_CONSTRAINTS: UploadConstraints = {
  allowedTypes: ["pdf"],
  maxFiles: 5,
  maxFileSizeMb: 10,
};

const toFileArray = (input: FileList | File[] | null): File[] | null => {
  if (!input) {
    return null;
  }
  const filesArray = Array.from(input as ArrayLike<File>);
  return filesArray.length > 0 ? filesArray : null;
};

const clamp = (value: number, min: number, max: number): number =>
  Math.min(max, Math.max(min, value));

const parseAllowedTypes = (raw: string | undefined): string[] => {
  if (!raw) return [];
  return raw
    .split(",")
    .map((value) => value.trim().toLowerCase())
    .filter((value) => value && value in FILE_TYPE_METADATA);
};

const toIntOrDefault = (
  raw: string | undefined,
  fallback: number,
  min: number,
  max: number,
): number => {
  const parsed = Number.parseInt(raw ?? "", 10);
  if (Number.isNaN(parsed)) {
    return fallback;
  }
  return clamp(parsed, min, max);
};

const deriveConstraints = (
  values: Partial<Record<string, string>> | null,
): UploadConstraints => {
  const allowed = parseAllowedTypes(values?.UPLOAD_ALLOWED_FILE_TYPES);
  const maxFiles = toIntOrDefault(
    values?.UPLOAD_MAX_FILES,
    DEFAULT_CONSTRAINTS.maxFiles,
    1,
    20,
  );
  const maxFileSizeMb = toIntOrDefault(
    values?.UPLOAD_MAX_FILE_SIZE_MB,
    DEFAULT_CONSTRAINTS.maxFileSizeMb,
    1,
    200,
  );

  return {
    allowedTypes:
      allowed.length > 0
        ? allowed
        : [...DEFAULT_CONSTRAINTS.allowedTypes],
    maxFiles,
    maxFileSizeMb,
  };
};

const constraintsEqual = (a: UploadConstraints, b: UploadConstraints): boolean => {
  if (a.maxFiles !== b.maxFiles || a.maxFileSizeMb !== b.maxFileSizeMb) {
    return false;
  }
  if (a.allowedTypes.length !== b.allowedTypes.length) {
    return false;
  }
  return a.allowedTypes.every((value, index) => value === b.allowedTypes[index]);
};

const extensionOf = (name: string): string => {
  const lastDot = name.lastIndexOf(".");
  if (lastDot === -1) return "";
  return name.slice(lastDot).toLowerCase();
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

  const [constraints, setConstraints] = useState<UploadConstraints>({
    allowedTypes: [...DEFAULT_CONSTRAINTS.allowedTypes],
    maxFiles: DEFAULT_CONSTRAINTS.maxFiles,
    maxFileSizeMb: DEFAULT_CONSTRAINTS.maxFileSizeMb,
  });
  const [isDragOver, setIsDragOver] = useState(false);
  const isCancellingRef = useRef(false);

  useEffect(() => {
    let active = true;

    const applyConstraints = (values: Partial<Record<string, string>> | null) => {
      if (!active) return;
      const next = deriveConstraints(values);
      setConstraints((prev) => (constraintsEqual(prev, next) ? prev : next));
    };

    if (typeof window !== "undefined") {
      applyConstraints(loadConfigFromStorage());
    }

    void (async () => {
      try {
        const remoteValues = await ConfigurationService.getConfigValuesConfigValuesGet();
        if (!active) return;
        applyConstraints(remoteValues as Record<string, string>);
      } catch (err) {
        logger.warn('Failed to fetch runtime configuration values', { error: err });
      }
    })();

    if (typeof window !== "undefined") {
      const listener = () => {
        applyConstraints(loadConfigFromStorage());
      };
      // Refetch from backend when config is synced on startup
      const syncListener = async () => {
        try {
          const remoteValues = await ConfigurationService.getConfigValuesConfigValuesGet();
          if (!active) return;
          applyConstraints(remoteValues as Record<string, string>);
        } catch (err) {
          logger.warn('Failed to fetch runtime configuration values after sync', { error: err });
        }
      };
      window.addEventListener(RUNTIME_CONFIG_EVENT, listener);
      window.addEventListener(RUNTIME_CONFIG_SYNCED_EVENT, syncListener);
      return () => {
        active = false;
        window.removeEventListener(RUNTIME_CONFIG_EVENT, listener);
        window.removeEventListener(RUNTIME_CONFIG_SYNCED_EVENT, syncListener);
      };
    }

    return () => {
      active = false;
    };
  }, []);

  const allowedTypeMeta = useMemo(() => {
    return constraints.allowedTypes
      .map((type) => FILE_TYPE_METADATA[type])
      .filter((meta): meta is FileTypeMeta => Boolean(meta));
  }, [constraints.allowedTypes]);

  const allowedFileTypesLabel = useMemo(() => {
    if (allowedTypeMeta.length > 0) {
      return allowedTypeMeta.map((meta) => meta.label).join(", ");
    }
    return FILE_TYPE_METADATA.pdf.label;
  }, [allowedTypeMeta]);

  const fileAccept = useMemo(() => {
    const patterns = new Set<string>();
    const source =
      allowedTypeMeta.length > 0
        ? allowedTypeMeta
        : [FILE_TYPE_METADATA.pdf];
    source.forEach((meta) => {
      meta.extensions.forEach((ext) => patterns.add(ext));
      meta.mimeTypes.forEach((mime) => patterns.add(mime));
    });
    return Array.from(patterns).join(",");
  }, [allowedTypeMeta]);

  const maxFileSizeBytes = useMemo(
    () => constraints.maxFileSizeMb * MB_IN_BYTES,
    [constraints.maxFileSizeMb],
  );

  // Reset cancelling flag after cancellation completes
  useEffect(() => {
    if (!uploading && isCancellingRef.current) {
      const timer = setTimeout(() => {
        isCancellingRef.current = false;
      }, 500);
      return () => clearTimeout(timer);
    }
  }, [uploading]);

  const validateFiles = useCallback(
    (candidate: File[]) => {
      if (candidate.length > constraints.maxFiles) {
        const message = `Select up to ${constraints.maxFiles} file${constraints.maxFiles === 1 ? "" : "s"} per upload.`;
        toast.error("Too many files selected", { description: message });
        setError(message);
        return false;
      }

      const allowedExtensions = new Set<string>();
      const allowedMimeTypes = new Set<string>();
      const metaSource =
        allowedTypeMeta.length > 0
          ? allowedTypeMeta
          : [FILE_TYPE_METADATA.pdf];

      metaSource.forEach((meta) => {
        meta.extensions.forEach((ext) => allowedExtensions.add(ext.toLowerCase()));
        meta.mimeTypes.forEach((mime) => allowedMimeTypes.add(mime.toLowerCase()));
      });

      for (const file of candidate) {
        if (file.size > maxFileSizeBytes) {
          const message = `'${file.name || "File"}' is ${(file.size / MB_IN_BYTES).toFixed(1)} MB. Maximum allowed is ${constraints.maxFileSizeMb} MB per file.`;
          toast.error("File too large", { description: message });
          setError(message);
          return false;
        }

        const extension = extensionOf(file.name || "");
        const mime = (file.type || "").toLowerCase();
        const matchesExtension = extension && allowedExtensions.has(extension);
        const matchesMime = mime && allowedMimeTypes.has(mime);
        if (
          (allowedExtensions.size > 0 || allowedMimeTypes.size > 0) &&
          !matchesExtension &&
          !matchesMime
        ) {
          const message = `'${file.name || "File"}' must be ${allowedFileTypesLabel}.`;
          toast.error("Unsupported file type", { description: message });
          setError(message);
          return false;
        }
      }

      setError(null);
      return true;
    },
    [
      allowedFileTypesLabel,
      allowedTypeMeta,
      constraints.maxFiles,
      constraints.maxFileSizeMb,
      maxFileSizeBytes,
      setError,
    ],
  );

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragOver(false);
      const droppedFiles = toFileArray(e.dataTransfer.files);
      if (droppedFiles && droppedFiles.length > 0) {
        if (validateFiles(droppedFiles)) {
          setFiles(droppedFiles);
        } else {
          setFiles(null);
        }
      }
    },
    [setFiles, validateFiles],
  );

  const handleFileSelect = useCallback(
    (selectedFiles: FileList | File[] | null) => {
      const nextFiles = toFileArray(selectedFiles);
      if (nextFiles) {
        if (validateFiles(nextFiles)) {
          setFiles(nextFiles);
        } else {
          setFiles(null);
        }
      } else {
        setFiles(null);
      }
    },
    [setFiles, validateFiles],
  );

  const handleUpload = useCallback(
    async (isReady: boolean) => {
      if (uploading || isCancellingRef.current) {
        logger.warn("Upload already in progress or cancelling, ignoring submission", {
          uploading,
          isCancelling: isCancellingRef.current
        });
        return;
      }

      if (!files || files.length === 0) return;
      if (!validateFiles(files)) {
        return;
      }

      if (!isReady) {
        toast.error("System Not Ready", {
          description: "Initialize collection and bucket before uploading",
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

        const startRes = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL || ""}/index`, {
          method: "POST",
          body: formData,
        });

        if (!startRes.ok) {
          const t = await startRes.text();
          throw new Error(`Failed to start indexing: ${startRes.status} ${t}`);
        }

        const startData = (await startRes.json()) as {
          status?: string;
          message?: string;
          job_id?: string;
          total?: number;
          skipped_count?: number;
          skipped_files?: string[];
        };

        // Handle case where all documents were already indexed (duplicates)
        if (startData.status === "completed" && !startData.job_id) {
          const skippedCount = startData.skipped_count || 0;
          const skippedFiles = startData.skipped_files || [];
          const message = startData.message || "All documents already indexed";

          setMessage(message);
          setStatusText(null);
          setProgress(100);
          setUploading(false);
          setFiles(null);

          toast.info("Documents Already Indexed", {
            description: skippedCount > 0
              ? `${skippedCount} file${skippedCount === 1 ? "" : "s"} already in the system: ${skippedFiles.join(", ")}`
              : message,
          });

          logger.info('Upload skipped: all documents already indexed', {
            skippedCount,
            skippedFiles
          });
          return;
        }

        const startedJobId: string = startData.job_id || "";
        const total: number = Number(startData.total ?? 0);
        setJobId(startedJobId);
        setStatusText(total > 0 ? `Queued ${total} pages` : "Preparing documents...");
      } catch (err: unknown) {
        setProgress(0);

        let errorMsg = "Upload failed";
        if (err instanceof ApiError) {
          errorMsg = `${err.status}: ${err.message}`;
          logger.error('Upload start failed', { error: err, status: err.status, fileCount: files.length });
        } else if (err instanceof Error) {
          errorMsg = err.message;
          logger.error('Upload start failed', { error: err, fileCount: files.length });
        }
        setError(errorMsg);
        toast.error("Upload Failed", {
          description: errorMsg,
        });
        setUploading(false);
      }
    },
    [
      files,
      uploading,
      validateFiles,
      setUploading,
      setProgress,
      setMessage,
      setError,
      setJobId,
      setStatusText,
    ],
  );

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

    fileCount:
      files && files.length > 0
        ? files.length
        : fileMeta && fileMeta.length > 0
          ? fileMeta.length
          : 0,
    hasFiles:
      (files && files.length > 0) ||
      (uploading && fileMeta && fileMeta.length > 0),

    allowedFileTypes: constraints.allowedTypes,
    allowedFileTypesLabel,
    maxFilesAllowed: constraints.maxFiles,
    maxFileSizeMb: constraints.maxFileSizeMb,
    fileAccept,

    handleDragOver,
    handleDragLeave,
    handleDrop,
    handleFileSelect,
    handleUpload,
    handleCancel,
    handleClear,
  };
}
