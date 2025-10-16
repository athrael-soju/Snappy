"use client"

import "@/lib/api/client"

import { Page, PageSection } from "@/components/layout/page"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  CardFooter,
} from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { useSystemStatus, useMaintenanceActions, useSystemManagement } from "@/lib/hooks"
import type { ActionType } from "@/lib/hooks/use-maintenance-actions"

const RESET_ACTIONS: Array<{
  id: ActionType
  title: string
  description: string
  confirm: string
}> = [
  {
    id: "all",
    title: "Reset all data",
    description: "Remove every stored document, embedding, and image.",
    confirm: "Reset the entire system? This permanently removes all data.",
  },
  {
    id: "q",
    title: "Clear Qdrant",
    description: "Delete the document vectors stored in Qdrant.",
    confirm: "Remove all vectors from Qdrant? This cannot be undone.",
  },
  {
    id: "m",
    title: "Clear MinIO",
    description: "Delete objects stored in the MinIO bucket (when enabled).",
    confirm: "Remove all objects from MinIO? This cannot be undone.",
  },
]

export default function MaintenancePage() {
  const { systemStatus, statusLoading, fetchStatus, isSystemReady } = useSystemStatus()
  const { loading, runAction } = useMaintenanceActions({ onSuccess: fetchStatus })
  const { initLoading, deleteLoading, handleInitialize, handleDelete } = useSystemManagement({
    onSuccess: fetchStatus,
  })

  const handleMaintenanceAction = (actionId: ActionType) => {
    const action = RESET_ACTIONS.find((item) => item.id === actionId)
    if (!action) return
    if (window.confirm(action.confirm)) {
      void runAction(actionId)
    }
  }

  const confirmDelete = () => {
    if (window.confirm("Delete the collection and (if enabled) the bucket? This cannot be undone.")) {
      void handleDelete()
    }
  }

  const headerActions = (
    <div className="flex flex-wrap gap-2">
      <Button
        variant="outline"
        size="sm"
        onClick={fetchStatus}
        disabled={statusLoading}
      >
        {statusLoading ? "Refreshing..." : "Refresh status"}
      </Button>
      <Button
        variant="destructive"
        size="sm"
        onClick={confirmDelete}
        disabled={deleteLoading || initLoading}
      >
        {deleteLoading ? "Deleting..." : "Delete storage"}
      </Button>
    </div>
  )

  return (
    <Page
      title="Maintenance"
      description="Monitor storage status and run maintenance operations against the FastAPI endpoints."
      actions={headerActions}
    >
      <PageSection>
        <Card>
          <CardHeader className="gap-3">
            <CardTitle>System overview</CardTitle>
            <CardDescription>
              Review whether storage is ready before performing destructive operations.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-(--space-section-stack)">
            <div className="flex flex-wrap items-center gap-3 text-sm text-muted-foreground">
              <Badge
                variant={isSystemReady ? "secondary" : "destructive"}
                data-state={isSystemReady ? "ready" : "not-ready"}
              >
                System ready: {isSystemReady ? "Yes" : "No"}
              </Badge>
            {statusLoading && <span>Fetching latest status...</span>}
            </div>

            <div className="grid gap-(--space-section-stack) sm:grid-cols-2">
              <StatusPanel
                title="Collection"
                loading={statusLoading}
                items={
                  systemStatus?.collection
                    ? [
                        ["Name", systemStatus.collection.name],
                        ["Exists", systemStatus.collection.exists ? "Yes" : "No"],
                        ["Vectors", String(systemStatus.collection.vector_count)],
                        ["Files", String(systemStatus.collection.unique_files)],
                        systemStatus.collection.error
                          ? ["Error", systemStatus.collection.error]
                          : null,
                      ].filter(Boolean) as Array<[string, string]>
                    : undefined
                }
              />
              <StatusPanel
                title="Bucket"
                loading={statusLoading}
                items={
                  systemStatus?.bucket
                    ? [
                        ["Name", systemStatus.bucket.name],
                        ["Exists", systemStatus.bucket.exists ? "Yes" : "No"],
                        ["Objects", String(systemStatus.bucket.object_count)],
                        ["Disabled", systemStatus.bucket.disabled ? "Yes" : "No"],
                        systemStatus.bucket.error
                          ? ["Error", systemStatus.bucket.error]
                          : null,
                      ].filter(Boolean) as Array<[string, string]>
                    : undefined
                }
              />
            </div>
          </CardContent>
        </Card>
      </PageSection>

      <PageSection>
        <Card>
          <CardHeader className="gap-3">
            <CardTitle>Core operations</CardTitle>
            <CardDescription>
              Initialize or tear down shared storage resources used by the system.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-(--space-section-stack)">
            <div className="flex flex-wrap gap-3">
              <Button
                onClick={() => void handleInitialize()}
                disabled={initLoading || deleteLoading}
              >
                {initLoading ? "Initializing..." : "Initialize storage"}
              </Button>
            </div>
            <p className="text-xs text-muted-foreground">
              Initialization prepares the Qdrant collection and optionally the MinIO bucket. Deletion removes those
              resources and is available from the page actions above.
            </p>
          </CardContent>
        </Card>
      </PageSection>

      <PageSection>
        <Card>
          <CardHeader className="gap-3">
            <CardTitle>Reset actions</CardTitle>
            <CardDescription>
              Clear data from specific backends. Confirm each action before continuing.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid gap-(--space-section-stack) sm:grid-cols-2 lg:grid-cols-3">
              {RESET_ACTIONS.map((action) => (
                <Card key={action.id}>
                  <CardHeader className="gap-2">
                    <CardTitle className="text-base">{action.title}</CardTitle>
                    <CardDescription>{action.description}</CardDescription>
                  </CardHeader>
                  <CardFooter>
                    <Button
                      variant="destructive"
                      size="sm"
                      onClick={() => handleMaintenanceAction(action.id)}
                      disabled={loading[action.id] || initLoading || deleteLoading}
                    >
                      {loading[action.id] ? "Running..." : "Run action"}
                    </Button>
                  </CardFooter>
                </Card>
              ))}
            </div>
          </CardContent>
        </Card>
      </PageSection>
    </Page>
  )
}

type StatusPanelProps = {
  title: string
  loading: boolean
  items?: Array<[string, string]>
}

function StatusPanel({ title, loading, items }: StatusPanelProps) {
  return (
    <Card className="border-border/40 shadow-none">
      <CardHeader className="gap-1">
        <CardTitle className="text-sm">{title}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-1 text-xs text-muted-foreground">
        {loading ? (
          <p>Loading...</p>
        ) : items && items.length > 0 ? (
          <ul className="space-y-1">
            {items.map(([label, value]) => (
              <li key={label}>
                <span className="font-medium text-foreground">{label}:</span> {value}
              </li>
            ))}
          </ul>
        ) : (
          <p>No information available.</p>
        )}
      </CardContent>
    </Card>
  )
}
