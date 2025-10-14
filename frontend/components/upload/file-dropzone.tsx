import { useRef } from "react";
import { motion } from "framer-motion";
import { FolderOpen, FileText, ArrowUpFromLine, XCircle, UploadCloud } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";
import { Card, CardContent } from "@/components/ui/card";
import { FileList } from "./file-list";
import { UploadProgress } from "./upload-progress";
import { UploadStatusAlerts } from "./upload-status-alerts";

interface FileDropzoneProps {
  isDragOver: boolean;
  uploading: boolean;
  files: FileList | null;
  fileCount: number;
  hasFiles: boolean;
  uploadProgress: number;
  statusText: string | null;
  jobId: string | null;
  message: string | null;
  error: string | null;
  isReady: boolean;
  onDragOver: (e: React.DragEvent) => void;
  onDragLeave: (e: React.DragEvent) => void;
  onDrop: (e: React.DragEvent) => void;
  onFileSelect: (files: FileList | null) => void;
  onSubmit: (e: React.FormEvent) => void;
  onCancel: () => void;
}

const containerMotion = {
  initial: { opacity: 0, y: 12 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.25, ease: "easeOut" },
};

export function FileDropzone({
  isDragOver,
  uploading,
  files,
  fileCount,
  hasFiles,
  uploadProgress,
  statusText,
  jobId,
  message,
  error,
  isReady,
  onDragOver,
  onDragLeave,
  onDrop,
  onFileSelect,
  onSubmit,
  onCancel,
}: FileDropzoneProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const uploadLabel = hasFiles
    ? `Upload ${fileCount} file${fileCount !== 1 ? "s" : ""}`
    : "Upload documents";

  return (
    <motion.div {...containerMotion}>
      <Card
        className={cn(
          "border-dashed transition-colors",
          isDragOver ? "border-primary bg-primary/5" : "border-muted hover:border-primary/50"
        )}
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        onDrop={onDrop}
      >
        <CardContent className="space-y-6 p-6 sm:p-8">
          <div className="flex flex-col items-center gap-4 text-center">
            <div
              className={cn(
                "flex size-16 items-center justify-center rounded-full bg-primary/10 text-primary transition-transform",
                isDragOver && "scale-105"
              )}
            >
              <UploadCloud className="h-7 w-7" aria-hidden="true" />
            </div>
            <div className="space-y-2">
              <h2 className="text-xl font-semibold text-foreground sm:text-2xl">
                {isDragOver ? "Release to upload" : "Drag files here"}
              </h2>
              <p className="mx-auto max-w-xl text-sm text-muted-foreground sm:text-base">
                Drop PDFs or images to feed Snappy’s indexer, or browse to select files from your device.
              </p>
            </div>
          </div>

          <form id="upload-form" onSubmit={onSubmit} className="space-y-6" noValidate>
            <div className="grid gap-3 sm:grid-cols-[minmax(0,1fr)_auto]">
              <Button
                type="button"
                variant="outline"
                className="h-12 justify-center rounded-lg"
                onClick={() => fileInputRef.current?.click()}
                disabled={uploading}
              >
                <FolderOpen className="mr-2 h-5 w-5" />
                Browse files
              </Button>

              {hasFiles && (
                <div className="flex items-center justify-center gap-2 rounded-lg border border-primary/40 bg-primary/10 px-4 py-2 text-sm font-medium text-primary">
                  <FileText className="h-4 w-4" aria-hidden="true" />
                  {fileCount} file{fileCount !== 1 ? "s" : ""} selected
                </div>
              )}
            </div>

            <Input
              ref={fileInputRef}
              type="file"
              multiple
              onChange={(e) => onFileSelect(e.target.files)}
              className="hidden"
              disabled={uploading}
              accept=".pdf,.doc,.docx,.txt,.png,.jpg,.jpeg,.gif"
            />

            <FileList files={files} hasFiles={hasFiles} />

            <UploadProgress
              uploading={uploading}
              progress={uploadProgress}
              statusText={statusText}
              jobId={jobId}
            />
          </form>

          <UploadStatusAlerts message={message} error={error} />

          <div className="space-y-3 border-t border-muted pt-4">
            {!isReady && !uploading && (
              <p className="text-center text-sm text-muted-foreground">
                Initialize the system before uploading new files.
              </p>
            )}

            <Button
              type={uploading ? "button" : "submit"}
              form="upload-form"
              disabled={!uploading && (!hasFiles || !isReady)}
              className="h-12 w-full rounded-lg text-base font-semibold"
              onClick={uploading ? onCancel : undefined}
              title={!isReady && !uploading ? "Snappy must be initialized before uploading" : undefined}
              variant={uploading ? "destructive" : "default"}
            >
              {uploading ? (
                <>
                  <XCircle className="mr-2 h-5 w-5" />
                  Cancel upload
                </>
              ) : (
                <>
                  <ArrowUpFromLine className="mr-2 h-5 w-5" />
                  {uploadLabel}
                </>
              )}
            </Button>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}
