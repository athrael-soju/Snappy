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
    <div className="space-y-4 sm:space-y-6">
        <div
          onDragOver={onDragOver}
          onDragLeave={onDragLeave}
          onDrop={onDrop}
          className={cn(
            "relative rounded-2xl border-2 border-dashed transition-all duration-300 bg-gradient-to-br from-background/50 to-background/30 backdrop-blur-sm",
            isDragOver 
              ? "border-primary/60 bg-primary/5 scale-[1.01] shadow-xl" 
              : "border-border/30 hover:border-border/50"
          )}
        >
          <div className="flex flex-col items-center gap-5 py-12 sm:py-16 px-4 sm:px-8 text-center">
            <div className={cn(
              "flex size-16 sm:size-20 items-center justify-center rounded-2xl bg-gradient-to-br from-primary/10 to-primary/5 text-primary transition-all duration-300",
              isDragOver && "scale-110 from-primary/20 to-primary/10"
            )}>
              <UploadCloud className="h-8 w-8 sm:h-10 sm:w-10" />
            </div>
            <div className="space-y-2.5">
              <h2 className="text-xl sm:text-2xl font-semibold">
                {isDragOver ? "Release to upload" : "Drag files here"}
              </h2>
              <p className="text-sm sm:text-base text-muted-foreground max-w-xl">
                Drop PDFs, images, or office documents to add them to your ColPali index. You can also browse from your device.
              </p>
            </div>
          </div>

          <div className="space-y-4 px-4 sm:px-6 pb-6 sm:pb-8">
          <form id="upload-form" onSubmit={onSubmit} className="space-y-4" noValidate>
            <div className="flex flex-col sm:flex-row gap-3">
              <Button
                type="button"
                variant="outline"
                size="lg"
                className="flex-1 h-11"
                onClick={() => fileInputRef.current?.click()}
                disabled={uploading}
              >
                <FolderOpen className="mr-2 h-4 w-4" />
                Browse files
              </Button>

              {hasFiles && (
                <Badge variant="secondary" className="flex items-center justify-center gap-1.5 px-3 py-2.5 h-auto text-xs sm:text-sm whitespace-nowrap">
                  <FileText className="h-3.5 w-3.5" />
                  {fileCount} file{fileCount !== 1 ? "s" : ""}
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

          <div className="space-y-2 pt-2">
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
              className="w-full h-11"
              onClick={uploading ? onCancel : undefined}
              title={!isReady && !uploading ? "System must be initialized before uploading" : undefined}
            >
              {uploading ? (
                <>
                  <XCircle className="mr-2 h-4 w-4" />
                  Cancel Upload
                </>
              ) : (
                <>
                  <ArrowUpFromLine className="mr-2 h-4 w-4" />
                  {uploadLabel}
                </>
              )}
            </Button>
          </div>
          </div>
        </div>
    </div>
  );
}


