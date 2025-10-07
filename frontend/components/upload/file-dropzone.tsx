import { useRef } from "react";
import { motion } from "framer-motion";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { fadeInScale, hoverLift } from "@/lib/motion-presets";
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

const MotionCard = motion(Card);

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
    <MotionCard
      variants={fadeInScale}
      initial="hidden"
      animate="visible"
      {...hoverLift}
      className={cn(
        "card-surface relative overflow-hidden border border-dashed border-muted/80 transition-all duration-200",
        isDragOver
          ? "border-primary/70 bg-primary/5 shadow-[var(--shadow-2)]"
          : "hover:border-primary/40 hover:shadow-[var(--shadow-2)]"
      )}
    >
      <div
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        onDrop={onDrop}
        className="h-full"
      >
        <CardHeader className="flex flex-col items-center gap-4 py-10 text-center">
          <div
            className={cn(
              "flex size-16 items-center justify-center rounded-full border border-muted bg-[color:var(--surface-2)] text-primary transition-all",
              isDragOver && "scale-105 border-primary/60 text-primary"
            )}
          >
            <UploadCloud className="h-7 w-7" aria-hidden="true" />
          </div>
          <div className="space-y-2">
            <CardTitle className="text-2xl font-semibold text-foreground">
              {isDragOver ? "Release to upload" : "Drag files here"}
            </CardTitle>
            <CardDescription className="mx-auto max-w-xl text-base leading-relaxed text-muted-foreground">
              Drop PDFs, images, or office documents to add them to your ColPali index. You can also browse from your device.
            </CardDescription>
          </div>
        </CardHeader>

        <CardContent className="space-y-8 px-6 pb-8">
          <form onSubmit={onSubmit} className="space-y-6" noValidate>
            <div className="space-y-3">
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-[minmax(0,1fr)_auto]">
                <Button
                  type="button"
                  variant="outline"
                  className="h-12 justify-center rounded-xl border border-muted text-foreground hover:border-primary/40 hover:bg-primary/10 focus-visible:ring-2 focus-visible:ring-ring/40"
                  onClick={() => fileInputRef.current?.click()}
                  disabled={uploading}
                >
                  <FolderOpen className="mr-2 h-5 w-5" />
                  Browse files
                </Button>

                {hasFiles && (
                  <div className="flex items-center justify-center gap-2 rounded-xl border border-muted bg-[color:var(--surface-2)] px-4 py-2 text-sm font-medium text-foreground">
                    <FileText className="h-4 w-4 text-muted-foreground" aria-hidden="true" />
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
            </div>

            <FileList files={files} hasFiles={hasFiles} />

            <UploadProgress
              uploading={uploading}
              progress={uploadProgress}
              statusText={statusText}
              jobId={jobId}
            />

            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              {!isReady && !uploading && (
                <p className="text-sm text-muted-foreground">
                  Initialize collections before uploading new content.
                </p>
              )}
              <div className="flex w-full gap-2 sm:w-auto">
                <Button
                  type={uploading ? "button" : "submit"}
                  disabled={!uploading && (!hasFiles || !isReady)}
                  className={cn(
                    "h-12 flex-1 rounded-full px-8 text-base font-semibold shadow-lg transition-all",
                    uploading
                      ? "bg-destructive text-white hover:bg-destructive/90"
                      : "primary-gradient hover:shadow-xl hover:scale-105"
                  )}
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
          </form>

          <UploadStatusAlerts message={message} error={error} />
        </CardContent>
      </div>
    </MotionCard>
  );
}


