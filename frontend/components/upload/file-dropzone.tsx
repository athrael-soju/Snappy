import { useRef } from "react";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { fadeInScale, hoverLift } from "@/lib/motion-presets";
import { FolderOpen, FileText, ArrowUpFromLine, XCircle, UploadCloud } from "lucide-react";
import { FileList } from "./file-list";
import { UploadProgress } from "./upload-progress";
import { UploadStatusAlerts } from "./upload-status-alerts";
import { cn } from "@/lib/utils";
import { GlassPanel } from "@/components/ui/glass-panel";

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

const MotionDiv = motion.div;

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
    <MotionDiv
      variants={fadeInScale}
      initial="hidden"
      animate="visible"
      {...hoverLift}
    >
      <GlassPanel
        className={cn(
          "relative overflow-hidden transition-all duration-200",
          isDragOver
            ? "ring-2 ring-primary/70 bg-primary/5"
            : "hover:ring-1 hover:ring-primary/40"
        )}
      >
        <div
          onDragOver={onDragOver}
          onDragLeave={onDragLeave}
          onDrop={onDrop}
          className="h-full"
        >
          <div className="flex flex-col items-center gap-4 py-10 px-6 text-center">
            <div
              className={cn(
                "flex size-16 items-center justify-center rounded-full border border-muted bg-gradient-to-br from-primary/10 to-primary/5 text-primary transition-all",
                isDragOver && "scale-105 border-primary/60"
              )}
            >
              <UploadCloud className="h-7 w-7" aria-hidden="true" />
            </div>
            <div className="space-y-2">
              <h2 className="text-2xl font-semibold text-foreground">
                {isDragOver ? "Release to upload" : "Drag files here"}
              </h2>
              <p className="mx-auto max-w-xl text-base leading-relaxed text-muted-foreground">
                Drop PDFs, images, or office documents to add them to your Snappy library. You can also browse from your device.
              </p>
            </div>
          </div>

          <div className="space-y-6 px-6 pb-6">
          <form id="upload-form" onSubmit={onSubmit} className="space-y-6" noValidate>
            <div className="space-y-3">
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-[minmax(0,1fr)_auto]">
                <Button
                  type="button"
                  variant="outline"
                  className="h-12 justify-center rounded-xl border border-border/50 bg-card/40 backdrop-blur-sm text-foreground hover:border-primary/50 hover:bg-primary/10 hover:scale-[1.02] transition-all duration-200 focus-visible:ring-2 focus-visible:ring-ring/40"
                  onClick={() => fileInputRef.current?.click()}
                  disabled={uploading}
                >
                  <FolderOpen className="mr-2 h-5 w-5" />
                  Browse files
                </Button>

                {hasFiles && (
                  <div className="flex items-center justify-center gap-2 rounded-xl border border-border/50 bg-primary/5 backdrop-blur-sm px-4 py-2 text-sm font-semibold text-primary">
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
            </div>

            <FileList files={files} hasFiles={hasFiles} />

            <UploadProgress
              uploading={uploading}
              progress={uploadProgress}
              statusText={statusText}
              jobId={jobId}
            />

          </form>

          <UploadStatusAlerts message={message} error={error} />

          {/* Action Section */}
          <div className="space-y-3 pt-4 border-t border-border/30">
            {!isReady && !uploading && (
              <p className="text-sm text-center text-muted-foreground">
                Initialize collections before uploading new content.
              </p>
            )}
            <Button
              type={uploading ? "button" : "submit"}
              disabled={!uploading && (!hasFiles || !isReady)}
              form="upload-form"
              className={cn(
                "h-12 w-full rounded-full px-8 text-base font-semibold shadow-lg transition-all duration-200",
                uploading
                  ? "bg-destructive text-destructive-foreground hover:bg-destructive/90 hover:scale-[1.02]"
                  : "primary-gradient hover:shadow-xl hover:scale-[1.02] disabled:opacity-50 disabled:hover:scale-100"
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
        </div>
      </GlassPanel>
    </MotionDiv>
  );
}


