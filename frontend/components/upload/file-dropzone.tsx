import { useRef } from "react";
import { motion } from "framer-motion";
import { Card, CardContent, CardDescription, CardHeader } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { fadeInScale, hoverLift } from "@/lib/motion-presets";
import { FolderOpen, FileText, ArrowUpFromLine, XCircle } from "lucide-react";
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

  const baseClasses = "relative border-2 border-dashed transition-all duration-300 group";
  const dragActiveClasses = "border-blue-500 bg-blue-500/5 shadow-lg scale-[1.02]";
  const dragInactiveClasses = "card-surface hover:border-blue-400/50 hover:shadow-md";
  const uploadLabel = hasFiles
    ? "Upload " + fileCount + " File" + (fileCount !== 1 ? "s" : "")
    : "Upload Documents";

  return (
    <MotionCard
      variants={fadeInScale}
      initial="hidden"
      animate="visible"
      {...hoverLift}
      className={baseClasses + " " + (isDragOver ? dragActiveClasses : dragInactiveClasses)}
    >
      <div
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        onDrop={onDrop}
        className="relative"
      >
        <CardHeader className="text-center pb-6">
          <CardDescription className="text-base leading-relaxed max-w-md mx-auto">
            {isDragOver
              ? "📁 Release to upload your documents"
              : "Drag & drop your files here, or click to browse. Upload reports, contracts, or images for instant visual search."}
          </CardDescription>
        </CardHeader>

        <CardContent className="space-y-6">
          <form onSubmit={onSubmit} className="space-y-6">
            {/* File Selection */}
            <div className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <Button
                  type="button"
                  variant="outline"
                  className="h-12 border-dashed hover:border-blue-400 hover:bg-blue-50/50"
                  onClick={() => fileInputRef.current?.click()}
                  disabled={uploading}
                >
                  <FolderOpen className="w-5 h-5 mr-2" />
                  Browse Files
                </Button>

                {hasFiles && (
                  <div className="flex items-center gap-2 px-4 py-2 bg-muted/50 rounded-lg">
                    <FileText className="w-4 h-4 text-muted-foreground" />
                    <span className="text-sm font-medium">
                      {fileCount} file{fileCount !== 1 ? "s" : ""} selected
                    </span>
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

            {/* Selected Files Display */}
            <FileList files={files} hasFiles={hasFiles} />

            {/* Upload Progress */}
            <UploadProgress
              uploading={uploading}
              progress={uploadProgress}
              statusText={statusText}
              jobId={jobId}
            />

            {/* Upload/Cancel Button */}
            <Button
              type={uploading ? "button" : "submit"}
              onClick={uploading ? onCancel : undefined}
              disabled={!uploading && (!hasFiles || !isReady)}
              variant={uploading ? "destructive" : "default"}
              className={
                uploading
                  ? "w-full h-12 bg-red-600 hover:bg-red-700 rounded-full"
                  : "w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 h-12 rounded-full"
              }
              size="lg"
              title={!isReady && !uploading ? "System must be initialized before uploading" : ""}
            >
              {uploading ? (
                <>
                  <XCircle className="w-5 h-5 mr-2" />
                  Cancel Upload
                </>
              ) : (
                <>
                  <ArrowUpFromLine className="w-5 h-5 mr-2" />
                  {uploadLabel}
                </>
              )}
            </Button>
          </form>

          {/* Status Messages */}
          <UploadStatusAlerts message={message} error={error} />
        </CardContent>
      </div>
    </MotionCard>
  );
}
