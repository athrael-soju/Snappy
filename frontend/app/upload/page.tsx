"use client";

import { useState, useRef, useCallback } from "react";
import { IndexingService, ApiError } from "@/lib/api/generated";
import type { Body_index_index_post } from "@/lib/api/generated";
import "@/lib/api/client";
import { Label } from "@/components/ui/8bit/label";
import { Input } from "@/components/ui/8bit/input";
import { Button } from "@/components/ui/8bit/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/8bit/card";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/8bit/alert";
import { Badge } from "@/components/ui/8bit/badge";
import { Progress } from "@/components/ui/8bit/progress";
import { Upload, FileText, CheckCircle, AlertCircle, Loader2, CloudUpload, FolderOpen, ArrowUpFromLine, Zap, Shield, Info, Lightbulb } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { toast } from "sonner";

export default function UploadPage() {
  const [files, setFiles] = useState<FileList | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isDragOver, setIsDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

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
    setUploadProgress(0);
    setMessage(null);
    setError(null);
    
    // Simulate progress for better UX
    const progressInterval = setInterval(() => {
      setUploadProgress(prev => {
        if (prev >= 90) return prev;
        return prev + Math.random() * 10;
      });
    }, 300);
    
    try {
      const payload: Body_index_index_post = {
        files: Array.from(files) as Blob[],
      };
      await IndexingService.indexIndexPost(payload);
      
      clearInterval(progressInterval);
      setUploadProgress(100);
      
      const successMsg = `Successfully uploaded ${files.length} file(s)`;
      setMessage(successMsg);
      setFiles(null);
      toast.success("Upload Complete", { 
        description: successMsg 
      });
      
      // Reset the file input
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    } catch (err: unknown) {
      clearInterval(progressInterval);
      setUploadProgress(0);
      
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
      setTimeout(() => setUploadProgress(0), 2000);
    }
  }

  const fileCount = files ? files.length : 0;
  const hasFiles = fileCount > 0;

  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="space-y-6"
    >
      {/* Header */}
      <div className="space-y-4">
        <div className="flex items-center gap-3">
          <div className="p-3 bg-gradient-to-br from-primary/10 to-accent/10 rounded-lg border border-primary/20">
            <CloudUpload className="w-7 h-7 text-primary" />
          </div>
          <div>
            <h1 className="text-3xl font-bold bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">Upload Documents</h1>
            <p className="text-muted-foreground text-base">Add your documents for AI-powered visual search</p>
          </div>
        </div>
      </div>

      {/* Upload Card with Drag & Drop */}
      <Card 
        className={`relative border-2 border-dashed rounded-xl p-8 text-center transition-all duration-300 cursor-pointer ${
          isDragOver
            ? 'border-primary bg-primary/5 scale-102'
            : 'border-muted-foreground/25 hover:border-primary/50 hover:bg-primary/5'
        }`}
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        onDrop={onDrop}
      >
        <CardHeader className="text-center pb-6">
          <motion.div 
            animate={{ 
              scale: isDragOver ? 1.1 : 1,
              rotate: isDragOver ? 5 : 0
            }}
            className={`mx-auto w-20 h-20 rounded-full flex items-center justify-center mb-4 transition-all ${
              isDragOver ? 'bg-primary/20 border-2 border-primary/30' : 'bg-gradient-to-br from-primary/10 to-accent/10 border border-primary/20'
            }`}
          >
            <CloudUpload className={`w-10 h-10 transition-colors ${
              isDragOver ? 'text-primary' : 'text-primary'
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
                  className="h-12 border-dashed hover:border-ring hover:bg-accent/10"
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
                    <span>Uploading...</span>
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
              className="w-full bg-primary text-primary-foreground hover:bg-primary/90 h-12"
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
      </Card>

      {/* Info Section - Moved */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="flex items-center gap-3 p-3 bg-gradient-to-br from-primary/5 to-primary/10 rounded-lg border border-primary/20">
          <div className="p-2 bg-primary/10 rounded border border-primary/20">
            <FileText className="w-4 h-4 text-primary" />
          </div>
          <div>
            <div className="font-semibold text-foreground text-sm">Multiple Formats</div>
            <div className="text-xs text-muted-foreground">PDF, images, and more</div>
          </div>
        </div>
        <div className="flex items-center gap-3 p-3 bg-gradient-to-br from-accent/5 to-accent/10 rounded-lg border border-accent/20">
          <div className="p-2 bg-accent/10 rounded border border-accent/20">
            <Zap className="w-4 h-4 text-accent" />
          </div>
          <div>
            <div className="font-semibold text-foreground text-sm">Fast Processing</div>
            <div className="text-xs text-muted-foreground">AI-powered analysis</div>
          </div>
        </div>
        <div className="flex items-center gap-3 p-3 bg-gradient-to-br from-ring/5 to-ring/10 rounded-lg border border-ring/20">
          <div className="p-2 bg-ring/10 rounded border border-ring/20">
            <Shield className="w-4 h-4 text-ring" />
          </div>
          <div>
            <div className="font-semibold text-foreground text-sm">Secure Upload</div>
            <div className="text-xs text-muted-foreground">Privacy protected</div>
          </div>
        </div>
      </div>
    </motion.div>
  );
}
