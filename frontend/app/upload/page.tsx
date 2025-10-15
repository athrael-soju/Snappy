"use client";

import { FormEvent } from "react";
import "@/lib/api/client";
import { useSystemStatus } from "@/stores/app-store";
import { useFileUpload } from "@/lib/hooks/use-file-upload";

export default function UploadPage() {
  const { systemStatus, statusLoading, fetchStatus, isReady } = useSystemStatus();
  const {
    files,
    uploading,
    uploadProgress,
    message,
    error,
    jobId,
    statusText,
    isDragOver,
    fileCount,
    hasFiles,
    handleDragOver,
    handleDragLeave,
    handleDrop,
    handleFileSelect,
    handleUpload,
    handleCancel,
  } = useFileUpload();

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    await handleUpload(isReady);
  };

  const selectedFiles = files ? Array.from(files) : [];
  const readyLabel = isReady ? "System is ready for uploads." : "Initialize the collection and bucket before uploading.";

  return (
    <main className="mx-auto flex max-w-3xl flex-col gap-6 p-6">
      <header className="space-y-2">
        <h1 className="text-2xl font-semibold text-foreground">Upload Documents</h1>
        <p className="text-sm text-muted-foreground">
          Choose one or more files and submit them to the backend. Upload progress and job status will appear below.
        </p>
      </header>

      <section className="space-y-3 rounded border border-border p-4">
        <div className="flex flex-wrap items-center gap-3 text-sm text-muted-foreground">
          <span className={isReady ? "text-green-600 dark:text-green-400" : "text-red-600 dark:text-red-400"}>
            {readyLabel}
          </span>
          <button
            type="button"
            onClick={fetchStatus}
            className="rounded border border-border px-3 py-1 text-xs font-medium text-foreground transition-colors hover:bg-muted"
            disabled={statusLoading}
          >
            {statusLoading ? "Checking..." : "Refresh status"}
          </button>
        </div>
        {systemStatus && (
          <div className="grid gap-2 text-xs text-muted-foreground sm:grid-cols-2">
            <div className="rounded bg-muted p-2">
              <p className="font-semibold text-foreground">Collection</p>
              <p>Name: {systemStatus.collection?.name ?? "unknown"}</p>
              <p>Exists: {systemStatus.collection?.exists ? "yes" : "no"}</p>
              {typeof systemStatus.collection?.vector_count === "number" && (
                <p>Vectors: {systemStatus.collection.vector_count}</p>
              )}
            </div>
            <div className="rounded bg-muted p-2">
              <p className="font-semibold text-foreground">Bucket</p>
              <p>Status: {systemStatus.bucket?.disabled ? "disabled" : systemStatus.bucket?.exists ? "ready" : "missing"}</p>
              <p>Name: {systemStatus.bucket?.name ?? "unknown"}</p>
              {typeof systemStatus.bucket?.object_count === "number" && (
                <p>Objects: {systemStatus.bucket.object_count}</p>
              )}
            </div>
          </div>
        )}
      </section>

      <form
        className="space-y-4 rounded border border-border p-4"
        onSubmit={handleSubmit}
      >
        <label className="flex flex-col gap-1 text-sm text-foreground">
          Select files
          <input
            type="file"
            multiple
            onChange={(event) => handleFileSelect(event.target.files)}
            disabled={uploading}
            className="rounded border border-border px-3 py-2 text-sm"
          />
        </label>

        <div
          className={`flex min-h-[120px] flex-col items-center justify-center gap-2 rounded border border-dashed border-border p-4 text-sm ${
            isDragOver ? "bg-muted" : ""
          }`}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
        >
          <p className="text-foreground">Drag and drop files here</p>
          <p className="text-xs text-muted-foreground">You can also use the file picker above.</p>
        </div>

        {hasFiles && (
          <div className="space-y-2 text-sm text-foreground">
            <p className="font-semibold">Files ready to upload ({fileCount})</p>
            <ul className="space-y-1 rounded border border-border p-2 text-xs text-muted-foreground">
              {selectedFiles.map((file) => (
                <li key={file.name}>
                  {file.name} ({Math.round(file.size / 1024)} KB)
                </li>
              ))}
            </ul>
          </div>
        )}

        {typeof uploadProgress === "number" && uploadProgress > 0 && (
          <p className="text-sm text-muted-foreground">Progress: {Math.round(uploadProgress)}%</p>
        )}
        {statusText && <p className="text-sm text-muted-foreground">Status: {statusText}</p>}
        {jobId && <p className="text-xs text-muted-foreground">Job ID: {jobId}</p>}
        {message && <p className="text-sm text-green-600 dark:text-green-400">{message}</p>}
        {error && <p className="text-sm text-red-600 dark:text-red-400">{error}</p>}

        <div className="flex flex-wrap gap-3">
          <button
            type="submit"
            className="rounded bg-primary px-4 py-2 text-sm font-medium text-primary-foreground disabled:opacity-50"
            disabled={!hasFiles || uploading || !isReady}
          >
            {uploading ? "Uploading..." : "Start upload"}
          </button>
          {uploading && (
            <button
              type="button"
              onClick={handleCancel}
              className="rounded border border-border px-4 py-2 text-sm font-medium text-foreground"
            >
              Cancel upload
            </button>
          )}
        </div>
      </form>
    </main>
  );
}
