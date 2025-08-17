"use client";

import { useState } from "react";
import { IndexingService, ApiError } from "@/lib/api/generated";
import type { Body_index_index_post } from "@/lib/api/generated";
import "@/lib/api/client";

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
        <input
          id="file-input"
          type="file"
          multiple
          onChange={(e) => setFiles(e.target.files)}
          className="block w-full text-sm"
        />
        <button
          type="submit"
          disabled={uploading || !files || files.length === 0}
          className="bg-black text-white dark:bg-white dark:text-black rounded px-4 py-2 text-sm"
        >
          {uploading ? "Uploading..." : "Upload"}
        </button>
      </form>
      {message && <div className="text-green-600 text-sm" role="status">{message}</div>}
      {error && <div className="text-red-600 text-sm" role="alert">{error}</div>}
    </div>
  );
}
