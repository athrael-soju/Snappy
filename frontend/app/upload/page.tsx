"use client";

import { useState } from "react";
import { IndexingService, ApiError } from "@/lib/api/generated";
import type { Body_index_index_post } from "@/lib/api/generated";
import "@/lib/api/client";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";

export default function UploadPage() {
  const [files, setFiles] = useState<FileList | null>(null);
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

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
      setMessage(`Uploaded ${files.length} file(s) successfully.`);
      setFiles(null);
      // Reset the file input visually
      const input = document.getElementById("file-input") as HTMLInputElement | null;
      if (input) input.value = "";
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        setError(`${err.status}: ${err.message}`);
      } else {
        setError("Upload failed");
      }
    } finally {
      setUploading(false);
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold">Upload</h1>
      <form onSubmit={onSubmit} className="space-y-3">
        <div className="space-y-1.5">
          <Label htmlFor="file-input">Select files</Label>
          <Input
            id="file-input"
            type="file"
            multiple
            onChange={(e) => setFiles(e.target.files)}
            className="block w-full text-sm"
          />
        </div>
        <Button type="submit" disabled={uploading || !files || files.length === 0}>
          {uploading ? (
            <span className="inline-flex items-center gap-2"><Spinner size={16} /> Uploading...</span>
          ) : (
            "Upload"
          )}
        </Button>
      </form>
      {message && <div className="text-green-600 text-sm" role="status">{message}</div>}
      {error && <div className="text-red-600 text-sm" role="alert">{error}</div>}
    </div>
  );
}
