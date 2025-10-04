"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { ApiError, MaintenanceService } from "@/lib/api/generated";
import "@/lib/api/client";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Upload, FileText, CheckCircle, AlertCircle, Loader2, CloudUpload, FolderOpen, ArrowUpFromLine, XCircle, AlertTriangle, ExternalLink } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { toast } from "@/components/ui/sonner";
import { useUploadStore, useSystemStatus } from "@/stores/app-store";
import { PageHeader } from "@/components/page-header";
import Link from "next/link";

export default function UploadPage() {
  // Use global upload store
  const {
    files,
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

  // Use system status
  const { systemStatus, setStatus, isReady, needsRefresh } = useSystemStatus();

  // Local state for UI interactions only
  const [isDragOver, setIsDragOver] = useState(false);
  const [statusLoading, setStatusLoading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const hasFetchedRef = useRef(false);
  const isCancellingRef = useRef(false);

  // Fetch system status function - always fetches fresh when called
  const fetchSystemStatus = useCallback(async () => {
    setStatusLoading(true);
    try {
      const status = await MaintenanceService.getStatusStatusGet();
      setStatus({ ...status, lastChecked: Date.now() });
      hasFetchedRef.current = true;
    } catch (err) {
      console.error('Failed to fetch system status:', err);
    } finally {
      setStatusLoading(false);
    }
  }, [setStatus]);

  // Fetch system status on mount and listen for changes
  useEffect(() => {
    // Only fetch if we haven't fetched yet
    if (!hasFetchedRef.current) {
      fetchSystemStatus();
    }

    // Listen for system status changes from other pages
    window.addEventListener('systemStatusChanged', fetchSystemStatus);
    
    return () => {
      window.removeEventListener('systemStatusChanged', fetchSystemStatus);
    };
  }, [fetchSystemStatus]);

  // Clear success/error messages after some time to avoid persistent state
  useEffect(() => {
    if (message && !uploading) {
      const timer = setTimeout(() => {
        setMessage(null);
      }, 10000); // Clear success message after 10 seconds
      return () => clearTimeout(timer);
    }
  }, [message, uploading, setMessage]);

  // Reset cancelling flag after cancellation completes
  useEffect(() => {
    if (!uploading && isCancellingRef.current) {
      // Short delay to ensure all state updates have settled
      const timer = setTimeout(() => {
        isCancellingRef.current = false;
      }, 500);
      return () => clearTimeout(timer);
    }
  }, [uploading]);

  useEffect(() => {
    if (error && !uploading) {
      const timer = setTimeout(() => {
        setError(null);
      }, 10000); // Clear error message after 10 seconds
      return () => clearTimeout(timer);
    }
  }, [error, uploading, setError]);

  // Drag and drop handlers
  const onDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const onDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    const droppedFiles = e.dataTransfer.files;
    if (droppedFiles.length > 0) {
      setFiles(droppedFiles);
    }
  };

  const handleFileSelect = (selectedFiles: FileList | null) => {
    if (selectedFiles) {
      setFiles(selectedFiles);
    }
  };

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    
    // Prevent re-submission while already uploading or cancelling
    if (uploading || isCancellingRef.current) {
      console.warn('Upload already in progress or cancelling, ignoring submission');
      return;
    }
    
    if (!files || files.length === 0) return;
    
    // Check if system is ready
    if (!isReady) {
      toast.error('System Not Ready', { 
        description: 'Initialize collection and bucket before uploading' 
      });
      return;
    }
    
    isCancellingRef.current = false; // Reset cancel flag
    setUploading(true);
    setProgress(0);
    setMessage(null);
    setError(null);
    setStatusText('Uploading files...');
    setJobId(null);
    
    try {
      // Build multipart form data manually to hit /index/start
      const formData = new FormData();
      Array.from(files).forEach((f) => formData.append("files", f));

      // Use XMLHttpRequest to track upload progress
      const startData: any = await new Promise((resolve, reject) => {
        const xhr = new XMLHttpRequest();
        
        // Track upload progress
        xhr.upload.addEventListener('progress', (e) => {
          if (e.lengthComputable) {
            const percentComplete = (e.loaded / e.total) * 100;
            setProgress(percentComplete);
            setStatusText(`Uploading... ${Math.round(percentComplete)}%`);
          }
        });
        
        xhr.addEventListener('load', () => {
          if (xhr.status >= 200 && xhr.status < 300) {
            try {
              resolve(JSON.parse(xhr.responseText));
            } catch (e) {
              reject(new Error('Invalid JSON response'));
            }
          } else {
            reject(new Error(`Failed to start indexing: ${xhr.status} ${xhr.responseText}`));
          }
        });
        
        xhr.addEventListener('error', () => {
          reject(new Error('Network error during upload'));
        });
        
        xhr.open('POST', `${process.env.NEXT_PUBLIC_API_BASE_URL || ''}/index`);
        xhr.send(formData);
      });
      
      const startedJobId: string = startData.job_id;
      const total: number = startData.total ?? 0;
      const message: string = startData.message || `Processing ${total} pages...`;
      setJobId(startedJobId);
      setProgress(0); // Reset for indexing progress
      setStatusText(message);

      // The global SSE connection will handle progress updates
      // We just need to wait for completion since the global store manages it
      
    } catch (err: unknown) {
      setProgress(0);
      
      let errorMsg = "Upload failed";
      if (err instanceof ApiError) {
        errorMsg = `${err.status}: ${err.message}`;
      } else if (err instanceof Error) {
        errorMsg = err.message;
      }
      setError(errorMsg);
      toast.error("Upload Failed", { 
        description: errorMsg 
      });
      setUploading(false);
    }
  }

  const fileCount = files ? files.length : 0;
  const hasFiles = fileCount > 0;

  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="flex flex-col min-h-0 flex-1"
    >
      <PageHeader
        title="Upload Documents"
        description="Drag & drop or select files to add to your visual search index"
        icon={CloudUpload}
      />

      {/* Scrollable Content */}
      <div className="flex-1 min-h-0 overflow-y-auto custom-scrollbar pr-2">
        <div className="space-y-6 pb-6">

          {/* System Status Warning */}
          {systemStatus && !isReady && (
            <Alert className="border-amber-300 bg-amber-50">
              <AlertTriangle className="h-5 w-5 text-amber-600" />
              <AlertTitle className="text-amber-900 font-semibold">System Not Initialized</AlertTitle>
              <AlertDescription className="text-amber-800">
                The collection and bucket must be initialized before uploading files.
                <Link href="/maintenance" className="inline-flex items-center gap-1 ml-2 text-amber-900 font-medium underline hover:text-amber-950">
                  Go to Data Management
                  <ExternalLink className="w-3 h-3" />
                </Link>
              </AlertDescription>
            </Alert>
          )}

      {/* Upload Card with Drag & Drop */}
      <Card className={`relative border-2 border-dashed transition-all duration-300 group ${
        isDragOver 
          ? 'border-blue-500 bg-blue-500/5 shadow-lg scale-[1.02]' 
          : 'border-muted-foreground/25 hover:border-blue-400/50 hover:shadow-md'
      }`}>
        <div 
          onDragOver={onDragOver}
          onDragLeave={onDragLeave}
          onDrop={onDrop}
          className="relative"
        >
          <CardHeader className="text-center pb-6">
            <CardDescription className="text-base leading-relaxed max-w-md mx-auto">
              {isDragOver 
                ? '📁 Release to upload your documents' 
                : 'Drag & drop your files here, or click to browse. Upload reports, contracts, or images for instant visual search.'
              }
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
                      <span className="text-sm font-medium">{fileCount} file{fileCount !== 1 ? 's' : ''} selected</span>
                    </div>
                  )}
                </div>
                
                <Input
                  ref={fileInputRef}
                  type="file"
                  multiple
                  onChange={(e) => handleFileSelect(e.target.files)}
                  className="hidden"
                  disabled={uploading}
                  accept=".pdf,.doc,.docx,.txt,.png,.jpg,.jpeg,.gif"
                />
              </div>
              
              {/* Selected Files Display */}
              <AnimatePresence>
                {hasFiles && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: "auto" }}
                    exit={{ opacity: 0, height: 0 }}
                    className="space-y-2"
                  >
                    <Label className="text-sm font-medium">Selected Files:</Label>
                    <div className="max-h-32 overflow-y-auto space-y-2 p-3 bg-muted/30 rounded-lg">
                      {Array.from(files!).map((file, idx) => (
                        <div key={idx} className="flex items-center gap-2 text-sm">
                          <FileText className="w-4 h-4 text-muted-foreground" />
                          <span className="truncate flex-1">{file.name}</span>
                          <Badge variant="outline" className="text-xs">
                            {(file.size / 1024 / 1024).toFixed(1)}MB
                          </Badge>
                        </div>
                      ))}
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
              
              {/* Upload Progress */}
              <AnimatePresence>
                {uploading && (
                  <motion.div
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    className="space-y-2"
                  >
                    <div className="flex items-center justify-between text-sm">
                      <span className="font-medium">
                        {statusText || (jobId ? `Processing...` : 'Uploading...')}
                      </span>
                      {uploadProgress > 0 && <span className="text-muted-foreground">{Math.round(uploadProgress)}%</span>}
                    </div>
                    <Progress value={uploadProgress} className="h-2" />
                  </motion.div>
                )}
              </AnimatePresence>
              
              {/* Upload/Cancel Button (transforms based on state) */}
              <Button 
                type={uploading ? "button" : "submit"}
                onClick={uploading ? () => {
                  isCancellingRef.current = true;
                  cancelUpload();
                } : undefined}
                disabled={!uploading && (!hasFiles || !isReady)}
                variant={uploading ? "destructive" : "default"}
                className={uploading 
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
                    Upload {hasFiles ? `${fileCount} File${fileCount !== 1 ? 's' : ''}` : 'Documents'}
                  </>
                )}
              </Button>
            </form>

            {/* Status Messages */}
            <AnimatePresence>
              {message && (
                <motion.div 
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.95 }}
                >
                  <Alert variant="default" className="border-green-200 bg-green-50/50">
                    <CheckCircle className="h-4 w-4 text-green-600" />
                    <AlertTitle className="text-green-800">Upload Status</AlertTitle>
                    <AlertDescription className="text-green-700">{message}</AlertDescription>
                  </Alert>
                </motion.div>
              )}
              
              {error && (
                <motion.div 
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.95 }}
                >
                  <Alert variant="destructive">
                    <AlertCircle className="h-4 w-4" />
                    <AlertTitle>Upload Status</AlertTitle>
                    <AlertDescription>{error}</AlertDescription>
                  </Alert>
                </motion.div>
              )}
            </AnimatePresence>
          </CardContent>
        </div>
      </Card>

          {/* Info Section - Moved closer and more prominent */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
            <Card className="border-blue-200/50">
              <CardHeader className="pb-4">
                <div className="flex items-center gap-2">
                  <FileText className="w-5 h-5 text-blue-500" />
                  <CardTitle className="text-lg font-semibold">Supported Formats</CardTitle>
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <div className="font-medium text-foreground flex items-center gap-2">
                      <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                      Documents
                    </div>
                    <div className="text-sm text-muted-foreground pl-4">
                      PDF
                    </div>
                  </div>
                  <div className="space-y-2">
                    <div className="font-medium text-foreground flex items-center gap-2">
                      <div className="w-2 h-2 bg-purple-500 rounded-full"></div>
                      Images
                    </div>
                    <div className="text-sm text-muted-foreground pl-4">
                      PNG, JPG, JPEG, GIF
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
            
            <Card className="border-purple-200/50">
              <CardHeader className="pb-4">
                <div className="flex items-center gap-2">
                  <ArrowUpFromLine className="w-5 h-5 text-purple-500" />
                  <CardTitle className="text-lg font-semibold">Quick Tips</CardTitle>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-3 text-sm">
                  <div className="flex items-start gap-2">
                    <div className="w-1.5 h-1.5 bg-purple-500 rounded-full mt-2 flex-shrink-0"></div>
                    <span className="text-muted-foreground">Drag files directly from your computer</span>
                  </div>
                  <div className="flex items-start gap-2">
                    <div className="w-1.5 h-1.5 bg-purple-500 rounded-full mt-2 flex-shrink-0"></div>
                    <span className="text-muted-foreground">Upload multiple files at once</span>
                  </div>
                  <div className="flex items-start gap-2">
                    <div className="w-1.5 h-1.5 bg-purple-500 rounded-full mt-2 flex-shrink-0"></div>
                    <span className="text-muted-foreground">Files are processed automatically for search</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </motion.div>
  );
}
