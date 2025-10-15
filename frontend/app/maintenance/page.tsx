"use client";

import "@/lib/api/client";
import { useSystemStatus, useMaintenanceActions, useSystemManagement } from "@/lib/hooks";
import { MAINTENANCE_ACTIONS } from "@/components/maintenance/constants";

export default function MaintenancePage() {
  const { systemStatus, statusLoading, fetchStatus, isSystemReady } = useSystemStatus();
  const { loading, runAction } = useMaintenanceActions({ onSuccess: fetchStatus });
  const { initLoading, deleteLoading, handleInitialize, handleDelete } = useSystemManagement({ onSuccess: fetchStatus });

  const handleMaintenanceAction = (actionId: typeof MAINTENANCE_ACTIONS[number]["id"]) => {
    const action = MAINTENANCE_ACTIONS.find((item) => item.id === actionId);
    if (!action) return;
    if (window.confirm(action.confirmMsg)) {
      void runAction(actionId);
    }
  };

  const confirmDelete = () => {
    if (window.confirm("Delete the collection and (if enabled) the bucket? This cannot be undone.")) {
      void handleDelete();
    }
  };

  return (
    <main className="mx-auto flex max-w-5xl flex-col gap-6 p-6">
      <header className="space-y-2">
        <h1 className="text-2xl font-semibold text-foreground">System Maintenance</h1>
        <p className="text-sm text-muted-foreground">
          Monitor storage status and run destructive operations manually. Buttons below interact with the FastAPI maintenance endpoints without any decorative UI.
        </p>
        <div className="flex flex-wrap items-center gap-3 text-xs text-muted-foreground">
          <span>System ready: {isSystemReady ? "yes" : "no"}</span>
          <button
            type="button"
            onClick={fetchStatus}
            className="rounded border border-border px-3 py-1 font-medium text-foreground disabled:opacity-50"
            disabled={statusLoading}
          >
            {statusLoading ? "Refreshing..." : "Refresh status"}
          </button>
        </div>
      </header>

      <section className="space-y-3 rounded border border-border p-4 text-sm">
        <h2 className="text-base font-semibold text-foreground">Storage Status</h2>
        <div className="grid gap-3 sm:grid-cols-2">
          <article className="rounded border border-dashed border-border p-3">
            <h3 className="text-sm font-semibold text-foreground">Collection</h3>
            {statusLoading ? (
              <p className="text-xs text-muted-foreground">Loading...</p>
            ) : systemStatus?.collection ? (
              <ul className="space-y-1 text-xs text-muted-foreground">
                <li>Name: {systemStatus.collection.name}</li>
                <li>Exists: {systemStatus.collection.exists ? "yes" : "no"}</li>
                <li>Vectors: {systemStatus.collection.vector_count}</li>
                <li>Files: {systemStatus.collection.unique_files}</li>
                {systemStatus.collection.error && <li>Error: {systemStatus.collection.error}</li>}
              </ul>
            ) : (
              <p className="text-xs text-muted-foreground">No information available.</p>
            )}
          </article>

          <article className="rounded border border-dashed border-border p-3">
            <h3 className="text-sm font-semibold text-foreground">Bucket</h3>
            {statusLoading ? (
              <p className="text-xs text-muted-foreground">Loading...</p>
            ) : systemStatus?.bucket ? (
              <ul className="space-y-1 text-xs text-muted-foreground">
                <li>Name: {systemStatus.bucket.name}</li>
                <li>Exists: {systemStatus.bucket.exists ? "yes" : "no"}</li>
                <li>Objects: {systemStatus.bucket.object_count}</li>
                <li>Disabled: {systemStatus.bucket.disabled ? "yes" : "no"}</li>
                {systemStatus.bucket.error && <li>Error: {systemStatus.bucket.error}</li>}
              </ul>
            ) : (
              <p className="text-xs text-muted-foreground">No information available.</p>
            )}
          </article>
        </div>
      </section>

      <section className="space-y-3 rounded border border-border p-4 text-sm">
        <h2 className="text-base font-semibold text-foreground">Core Operations</h2>
        <div className="flex flex-wrap gap-3">
          <button
            type="button"
            onClick={() => void handleInitialize()}
            className="rounded bg-primary px-4 py-2 font-medium text-primary-foreground disabled:opacity-50"
            disabled={initLoading || deleteLoading}
          >
            {initLoading ? "Initializing..." : "Initialize storage"}
          </button>
          <button
            type="button"
            onClick={confirmDelete}
            className="rounded border border-red-500 px-4 py-2 font-medium text-red-600 disabled:opacity-50 dark:text-red-400"
            disabled={deleteLoading || initLoading}
          >
            {deleteLoading ? "Deleting..." : "Delete storage"}
          </button>
        </div>
        <p className="text-xs text-muted-foreground">
          Initialization prepares the Qdrant collection and optionally the MinIO bucket. Deletion removes those resources.
        </p>
      </section>

      <section className="space-y-3 rounded border border-border p-4 text-sm">
        <h2 className="text-base font-semibold text-foreground">Reset Actions</h2>
        <p className="text-xs text-muted-foreground">
          These operations clear data from specific backends. Confirm each action before continuing.
        </p>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {MAINTENANCE_ACTIONS.map((action) => (
            <article key={action.id} className="space-y-2 rounded border border-dashed border-border p-3">
              <h3 className="text-sm font-semibold text-foreground">{action.title}</h3>
              <p className="text-xs text-muted-foreground">{action.description}</p>
              <button
                type="button"
                onClick={() => handleMaintenanceAction(action.id)}
                className="rounded border border-border px-3 py-2 text-xs font-medium text-foreground disabled:opacity-50"
                disabled={loading[action.id] || initLoading || deleteLoading}
              >
                {loading[action.id] ? "Running..." : "Run action"}
              </button>
            </article>
          ))}
        </div>
      </section>
    </main>
  );
}

