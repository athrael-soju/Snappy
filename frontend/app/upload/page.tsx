"use client";

import { useState, useRef } from "react";
import { IndexingService, ApiError } from "@/lib/api/generated";
import type { Body_index_index_post } from "@/lib/api/generated";
import "@/lib/api/client";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Upload, FileText, CheckCircle, AlertCircle, Loader2 } from "lucide-react";
import { motion } from "framer-motion";
import { toast } from "sonner";

export default function UploadPage() {
  const [files, setFiles] = useState<FileList | null>(null);
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!files || files.length === 0) return;
    setUploading(true);
    setMessage(null);
    setError(null);
    
    try {
      const payload: Body_index_index_post = {
        files: Array.from(files) as Blob[],
      };
      await IndexingService.indexIndexPost(payload);
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
          <div className="p-2 bg-primary/10 rounded-lg">
            <Upload className="w-6 h-6 text-primary" />
          </div>
          <div>
            <h1 className="text-3xl font-bold">Upload Documents</h1>
            <p className="text-muted-foreground">Add documents to your visual search index</p>
          </div>
        </div>
      </div>

      {/* Upload Card */}
      <Card className="h-full border-2 border-dashed border-muted-foreground/25 hover:border-muted-foreground/50 transition-colors group">
        <CardHeader className="text-center">
          <div className="mx-auto w-16 h-16 bg-accent rounded-full flex items-center justify-center mb-4 group-hover:scale-105 transition-transform">
            <Upload className="w-8 h-8 text-muted-foreground group-hover:text-accent-foreground transition-colors" />
          </div>
          <CardTitle>Upload Documents</CardTitle>
          <CardDescription>
            Select PDF files to upload to your document collection
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <form onSubmit={onSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="file-input" className="text-sm font-medium">
                Files {hasFiles && `(${fileCount} selected)`}
              </Label>
              <Input
                ref={fileInputRef}
                id="file-input"
                type="file"
                multiple
                onChange={(e) => setFiles(e.target.files)}
                className="file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-primary file:text-primary-foreground hover:file:bg-primary/90 cursor-pointer"
                disabled={uploading}
              />
            </div>
            
            <Button 
              type="submit" 
              disabled={uploading || !hasFiles}
              className="w-full sm:w-auto"
              size="lg"
            >
              {uploading ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Uploading {fileCount} file{fileCount !== 1 ? 's' : ''}...
                </>
              ) : (
                <>
                  <Upload className="w-4 h-4 mr-2" />
                  Upload {hasFiles ? `${fileCount} file${fileCount !== 1 ? 's' : ''}` : 'Files'}
                </>
              )}
            </Button>
          </form>

          {/* Status Messages */}
          {message && (
            <motion.div 
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              className="flex items-center gap-2 p-3 bg-green-50 dark:bg-green-950/30 border border-green-200 dark:border-green-800 rounded-lg text-green-800 dark:text-green-200"
              role="status"
            >
              <CheckCircle className="w-4 h-4" />
              <span className="text-sm font-medium">{message}</span>
            </motion.div>
          )}
          
          {error && (
            <motion.div 
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              className="flex items-center gap-2 p-3 bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-800 rounded-lg text-red-800 dark:text-red-200"
              role="alert"
            >
              <AlertCircle className="w-4 h-4" />
              <span className="text-sm font-medium">{error}</span>
            </motion.div>
          )}
        </CardContent>
      </Card>

      {/* Info Section */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Supported Formats</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
            <div className="space-y-1">
              <div className="font-medium text-foreground">Documents</div>
              <div className="text-muted-foreground">PDF, DOC, DOCX, TXT</div>
            </div>
            <div className="space-y-1">
              <div className="font-medium text-foreground">Images</div>
              <div className="text-muted-foreground">PNG, JPG, JPEG, GIF</div>
            </div>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}
