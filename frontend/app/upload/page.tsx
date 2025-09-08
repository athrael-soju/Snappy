"use client";

import { useState, useRef, useCallback, useEffect } from "react";
import { ApiError } from "@/lib/api/generated";
import "@/lib/api/client";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Upload, FileText, CheckCircle, AlertCircle, Loader2, CloudUpload, FolderOpen, ArrowUpFromLine } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { toast } from "sonner";
import { useUploadStore } from "@/stores/app-store";

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
  } = useUploadStore();

  // Local state for UI interactions only
  const [isDragOver, setIsDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Clear success/error messages after some time to avoid persistent state
  useEffect(() => {
    if (message && !uploading) {
      const timer = setTimeout(() => {
        setMessage(null);
      }, 10000); // Clear success message after 10 seconds
      return () => clearTimeout(timer);
    }
  }, [message, uploading, setMessage]);

  useEffect(() => {
    if (error && !uploading) {
      const timer = setTimeout(() => {
        setError(null);
      }, 10000); // Clear error message after 10 seconds
      return () => clearTimeout(timer);
    }
  }, [error, uploading, setError]);

  // Drag and drop handlers
  const onDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  }, []);

  const onDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  }, []);

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    const droppedFiles = e.dataTransfer.files;
    if (droppedFiles.length > 0) {
      setFiles(droppedFiles);
    }
  }, []);

  const handleFileSelect = (selectedFiles: FileList | null) => {
    if (selectedFiles) {
      setFiles(selectedFiles);
    }
  };

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!files || files.length === 0) return;
    setUploading(true);
    setProgress(0);
    setMessage(null);
    setError(null);
    setStatusText(null);
    setJobId(null);
    
    try {
      // Build multipart form data manually to hit /index/start
      const formData = new FormData();
      Array.from(files).forEach((f) => formData.append("files", f));

      const startRes = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL || ''}/index`, {
        method: "POST",
        body: formData,
      });
      if (!startRes.ok) {
        const t = await startRes.text();
        throw new Error(`Failed to start indexing: ${startRes.status} ${t}`);
      }
      const startData = await startRes.json();
      const startedJobId: string = startData.job_id;
      const total: number = startData.total ?? 0;
      setJobId(startedJobId);
      setStatusText(`Queued ${total} pages`);

      // Subscribe to progress via SSE
      await new Promise<void>((resolve, reject) => {
        const es = new EventSource(`${process.env.NEXT_PUBLIC_API_BASE_URL || ''}/progress/stream/${startedJobId}`);

        const close = () => {
          try { es.close(); } catch {}
        };

        es.addEventListener('progress', (ev: MessageEvent) => {
          try {
            const data = JSON.parse(ev.data || '{}');
            const pct = Number(data.percent ?? 0);
            const tot = Number(data.total ?? total ?? 0);
            setProgress(pct);
            if (data.message) setStatusText(data.message);

            if (data.status === 'completed') {
              close();
              setProgress(100);
              const successMsg = data.message || `Indexed ${tot} page(s)`;
              setMessage(successMsg);
              setFiles(null);
              toast.success('Upload Complete', { description: successMsg });
              if (fileInputRef.current) fileInputRef.current.value = '';
              resolve();
            } else if (data.status === 'failed') {
              close();
              const errMsg = data.error || 'Indexing failed';
              setError(errMsg);
              toast.error('Upload Failed', { description: errMsg });
              reject(new Error(errMsg));
            }
          } catch (e) {
            // Ignore parse errors; will be handled by error listener if needed
          }
        });

        es.addEventListener('not_found', () => {
          close();
          const errMsg = 'Job not found';
          setError(errMsg);
          toast.error('Upload Failed', { description: errMsg });
          reject(new Error(errMsg));
        });

        es.addEventListener('error', () => {
          // EventSource automatically retries; only reject if already terminal? We keep it lenient.
          // If connection errors persist before any progress, surface a generic error.
          // Do not close here; let EventSource reconnect.
        });
      });
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
    } finally {
      setUploading(false);
      setTimeout(() => setProgress(0), 2000);
    }
  }

  const fileCount = files ? files.length : 0;
  const hasFiles = fileCount > 0;

  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="space-y-8"
    >
      {/* Header */}
      <div className="space-y-2">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-gradient-to-br from-blue-500/10 to-purple-500/10 rounded-lg border border-blue-500/20">
            <CloudUpload className="w-6 h-6 text-blue-500" />
          </div>
          <div>
            <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">Upload Documents</h1>
            <p className="text-muted-foreground">Drag & drop or select files to add to your visual search index</p>
          </div>
        </div>
      </div>

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
            <motion.div 
              animate={{ 
                scale: isDragOver ? 1.1 : 1,
                rotate: isDragOver ? 5 : 0
              }}
              className={`mx-auto w-20 h-20 rounded-full flex items-center justify-center mb-4 transition-all ${
                isDragOver ? 'bg-blue-500/20 border-2 border-blue-500/30' : 'bg-gradient-to-br from-blue-500/10 to-purple-500/10 border border-blue-500/20'
              }`}
            >
              <CloudUpload className={`w-10 h-10 transition-colors ${
                isDragOver ? 'text-blue-600' : 'text-blue-500'
              }`} />
            </motion.div>
            
            <CardTitle className="text-2xl mb-2">
              {isDragOver ? 'Drop your files here!' : 'Upload Documents'}
            </CardTitle>
            
            <CardDescription className="text-base leading-relaxed max-w-md mx-auto">
              {isDragOver 
                ? 'Release to upload your documents' 
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
                      <span>{statusText || (jobId ? `Indexing job ${jobId.slice(0, 8)}...` : 'Uploading...')}</span>
                      <span>{Math.round(uploadProgress)}%</span>
                    </div>
                    <Progress value={uploadProgress} className="h-2" />
                  </motion.div>
                )}
              </AnimatePresence>
              
              {/* Upload Button */}
              <Button 
                type="submit" 
                disabled={uploading || !hasFiles}
                className="w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 h-12"
                size="lg"
              >
                {uploading ? (
                  <>
                    <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                    Processing {fileCount} file{fileCount !== 1 ? 's' : ''}...
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
                    <AlertTitle className="text-green-800">Upload Successful</AlertTitle>
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
                    <AlertTitle>Upload Failed</AlertTitle>
                    <AlertDescription>{error}</AlertDescription>
                  </Alert>
                </motion.div>
              )}
            </AnimatePresence>
          </CardContent>
        </div>
      </Card>

      {/* Info Section - Moved closer and more prominent */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="border-blue-200/50">
          <CardHeader className="pb-4">
            <div className="flex items-center gap-2">
              <FileText className="w-5 h-5 text-blue-500" />
              <CardTitle className="text-lg">Supported Formats</CardTitle>
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
              <CardTitle className="text-lg">Quick Tips</CardTitle>
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
    </motion.div>
  );
}
