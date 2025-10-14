import { useRef } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { GlassPanel } from "@/components/ui/glass-panel";
import { FolderOpen, FileText, ArrowUpFromLine, XCircle, UploadCloud } from "lucide-react";
import { FileList } from "./file-list";
import { UploadProgress } from "./upload-progress";
import { UploadStatusAlerts } from "./upload-status-alerts";
import { cn } from "@/lib/utils";

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
    <GlassPanel
      className={cn(
        "border-2 border-dashed transition-all duration-300",
        isDragOver ? "border-primary/50 bg-primary/10 scale-[1.01] shadow-2xl" : "border-border/40"
      )}
      hover
    >
        <div
          onDragOver={onDragOver}
          onDragLeave={onDragLeave}
          onDrop={onDrop}
          className="h-full"
        >
          <div className="flex flex-col items-center gap-4 py-8 sm:py-12 px-6 sm:px-8 text-center">
            <div className={cn(
              "flex size-16 sm:size-20 items-center justify-center rounded-full icon-bg text-primary transition-all duration-300",
              isDragOver && "scale-110 bg-primary/20"
            )}>
              <UploadCloud className="h-8 w-8 sm:h-10 sm:w-10" />
            </div>
            <div className="space-y-2">
              <h2 className="text-xl sm:text-2xl font-semibold">
                {isDragOver ? "Release to upload" : "Drag files here"}
              </h2>
              <p className="text-sm sm:text-base text-muted-foreground max-w-2xl">
                Drop PDFs, images, or office documents to add them to your ColPali index. You can also browse from your device.
              </p>
            </div>
          </div>

          <div className="space-y-5 px-6 sm:px-8 pb-6 sm:pb-8">
          <form id="upload-form" onSubmit={onSubmit} className="space-y-4" noValidate>
            <div className="flex flex-col sm:flex-row gap-4">
              <Button
                type="button"
                variant="outline"
                size="lg"
                className="flex-1 h-12"
                onClick={() => fileInputRef.current?.click()}
                disabled={uploading}
              >
                <FolderOpen className="mr-2 h-5 w-5" />
                Browse files
              </Button>

              {hasFiles && (
                <Badge variant="secondary" className="flex items-center gap-2 px-4 py-3 h-auto text-sm">
                  <FileText className="h-4 w-4" />
                  {fileCount} file{fileCount !== 1 ? "s" : ""} selected
                </Badge>
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

          <div className="space-y-2 pt-3 border-t">
            {!isReady && !uploading && (
              <p className="text-xs text-center text-muted-foreground">
                Initialize collections before uploading new content.
              </p>
            )}
            <Button
              type={uploading ? "button" : "submit"}
              disabled={!uploading && (!hasFiles || !isReady)}
              form="upload-form"
              size="lg"
              variant={uploading ? "destructive" : "default"}
              className="w-full"
              onClick={uploading ? onCancel : undefined}
              title={!isReady && !uploading ? "System must be initialized before uploading" : undefined}
            >
              {uploading ? (
                <>
                  <XCircle className="mr-2 h-5 w-5" />
                  Cancel Upload
                </>
              ) : (
                <>
                  <ArrowUpFromLine className="mr-2 h-5 w-5" />
                  {uploadLabel}
                </>
              )}
            </Button>
          </div>
          </div>
        </div>
    </GlassPanel>
  );
}


