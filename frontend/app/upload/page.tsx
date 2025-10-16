"use client"

import { FormEvent } from "react"
import "@/lib/api/client"

import { Page, PageSection } from "@/components/layout/page"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { Progress } from "@/components/ui/progress"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { useSystemStatus } from "@/stores/app-store"
import { useFileUpload } from "@/lib/hooks/use-file-upload"

export default function UploadPage() {
  const { systemStatus, statusLoading, fetchStatus, isReady } = useSystemStatus()
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
  } = useFileUpload()

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault()
    await handleUpload(isReady)
  }

  const selectedFiles = files ? Array.from(files) : []
  const readinessLabel = isReady
    ? "System is ready for uploads."
    : "Initialize the collection and bucket before uploading."
  const readinessBadgeVariant = (isReady ? "secondary" : "destructive") as
    | "secondary"
    | "destructive"

  return (
    <Page
      title="Upload"
      description="Choose files to add to the index. Progress and job status updates appear after submission."
      actions={
        <Button
          variant="outline"
          size="sm"
          onClick={fetchStatus}
          disabled={statusLoading}
        >
          {statusLoading ? "Checking..." : "Refresh status"}
        </Button>
      }
    >
      <PageSection>
        <Card>
          <CardHeader className="gap-3">
            <CardTitle>System readiness</CardTitle>
            <CardDescription>
              Confirm the collection and bucket are prepared before uploading.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-(--space-section-stack)">
            <div className="flex flex-wrap items-center gap-3 text-sm text-muted-foreground">
              <Badge
                variant={readinessBadgeVariant}
                data-state={isReady ? "ready" : "pending"}
              >
                {isReady ? "Ready for uploads" : "Initialization required"}
              </Badge>
              <span>{readinessLabel}</span>
            </div>

            {systemStatus && (
              <div className="grid gap-(--space-section-stack) text-sm text-muted-foreground sm:grid-cols-2">
                <dl className="space-y-2 rounded-lg border border-border/60 bg-card/40 p-4">
                  <dt className="text-sm font-semibold text-foreground">
                    Collection
                  </dt>
                  <dd>Name: {systemStatus.collection?.name ?? "unknown"}</dd>
                  <dd>Exists: {systemStatus.collection?.exists ? "yes" : "no"}</dd>
                  {typeof systemStatus.collection?.vector_count === "number" && (
                    <dd>Vectors: {systemStatus.collection.vector_count}</dd>
                  )}
                </dl>
                <dl className="space-y-2 rounded-lg border border-border/60 bg-card/40 p-4">
                  <dt className="text-sm font-semibold text-foreground">
                    Bucket
                  </dt>
                  <dd>
                    Status:{" "}
                    {systemStatus.bucket?.disabled
                      ? "disabled"
                      : systemStatus.bucket?.exists
                        ? "ready"
                        : "missing"}
                  </dd>
                  <dd>Name: {systemStatus.bucket?.name ?? "unknown"}</dd>
                  {typeof systemStatus.bucket?.object_count === "number" && (
                    <dd>Objects: {systemStatus.bucket.object_count}</dd>
                  )}
                </dl>
              </div>
            )}
          </CardContent>
        </Card>
      </PageSection>

      <PageSection>
        <Card>
          <CardHeader className="gap-3">
            <CardTitle>Upload documents</CardTitle>
            <CardDescription>
              Drop files or select them manually, then start the upload.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-(--space-section-stack)">
            <form
              onSubmit={handleSubmit}
              className="flex flex-col gap-(--space-section-stack)"
            >
              <div className="flex flex-col gap-2">
                <Label htmlFor="file-input">Select files</Label>
                <Input
                  id="file-input"
                  type="file"
                  multiple
                  onChange={(event) => handleFileSelect(event.target.files)}
                  disabled={uploading}
                />
              </div>

              <div
                data-state={isDragOver ? "active" : "idle"}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                className="flex min-h-40 flex-col items-center justify-center gap-3 rounded-lg border border-dashed border-border bg-card/30 px-6 py-8 text-center text-sm text-muted-foreground transition-colors data-[state=active]:bg-muted"
              >
                <span className="text-foreground">Drag and drop files here</span>
                <span>You can also use the file picker above.</span>
              </div>

              {hasFiles && (
                <div className="flex flex-col gap-2">
                  <span className="text-sm font-semibold text-foreground">
                    Files ready to upload ({fileCount})
                  </span>
                  <ul className="divide-y divide-border rounded-lg border border-border/60 bg-card/30 text-sm text-muted-foreground">
                    {selectedFiles.map((file) => (
                      <li key={file.name} className="px-4 py-3">
                        {file.name} ({Math.round(file.size / 1024)} KB)
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {typeof uploadProgress === "number" && uploadProgress > 0 && (
                <div className="space-y-2 text-sm text-muted-foreground">
                  <span className="font-medium text-foreground">
                    Upload progress {Math.round(uploadProgress)}%
                  </span>
                  <Progress value={uploadProgress} />
                </div>
              )}

              {statusText && (
                <Alert>
                  <AlertTitle>Status update</AlertTitle>
                  <AlertDescription>{statusText}</AlertDescription>
                </Alert>
              )}

              {jobId && (
                <Badge variant="outline" className="w-fit">
                  Job ID {jobId}
                </Badge>
              )}

              {message && (
                <Alert>
                  <AlertTitle>Upload complete</AlertTitle>
                  <AlertDescription>{message}</AlertDescription>
                </Alert>
              )}

              {error && (
                <Alert variant="destructive">
                  <AlertTitle>Upload failed</AlertTitle>
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}

              <div className="flex flex-wrap gap-3">
                <Button
                  type="submit"
                  disabled={!hasFiles || uploading || !isReady}
                >
                  {uploading ? "Uploading..." : "Start upload"}
                </Button>
                {uploading && (
                  <Button
                    type="button"
                    variant="outline"
                    onClick={handleCancel}
                  >
                    Cancel upload
                  </Button>
                )}
              </div>
            </form>
          </CardContent>
        </Card>
      </PageSection>
    </Page>
  )
}
