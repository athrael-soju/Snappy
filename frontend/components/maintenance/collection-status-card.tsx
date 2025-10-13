import { Database } from "lucide-react";
import { StatusCard } from "./status-card";
import { CollectionStatus } from "@/components/maintenance/types";

interface CollectionStatusCardProps {
  status: CollectionStatus | null;
  isLoading: boolean;
}

export function CollectionStatusCard({ status, isLoading }: CollectionStatusCardProps) {
  const qdrantMode = status?.embedded ? "Embedded (in-memory)" : "External service";
  const imageMode =
    status?.image_store_mode === "minio"
      ? "MinIO URLs"
      : status?.image_store_mode === "inline"
        ? "Base64 payloads"
        : "Unknown";

  const details = status ? (
    <div className="space-y-2 text-sm">
      <div className="flex justify-between items-center p-2 bg-blue-50 dark:bg-blue-950/40 rounded border border-blue-100 dark:border-blue-900/50">
        <span className="text-muted-foreground font-medium">Collection Name:</span>
        <span className="font-semibold text-foreground">{status.name}</span>
      </div>
      <div className="flex justify-between items-center p-2 bg-blue-50 dark:bg-blue-950/40 rounded border border-blue-100 dark:border-blue-900/50">
        <span className="text-muted-foreground font-medium">Vector Count:</span>
        <span className="font-semibold text-foreground">{status.vector_count.toLocaleString()}</span>
      </div>
      <div className="flex justify-between items-center p-2 bg-blue-50 dark:bg-blue-950/40 rounded border border-blue-100 dark:border-blue-900/50">
        <span className="text-muted-foreground font-medium">Unique Files:</span>
        <span className="font-semibold text-foreground">{status.unique_files.toLocaleString()}</span>
      </div>
      <div className="flex justify-between items-center p-2 bg-blue-50 dark:bg-blue-950/40 rounded border border-blue-100 dark:border-blue-900/50">
        <span className="text-muted-foreground font-medium">Qdrant Mode:</span>
        <span className="font-semibold text-foreground">{qdrantMode}</span>
      </div>
      <div className="flex justify-between items-center p-2 bg-blue-50 dark:bg-blue-950/40 rounded border border-blue-100 dark:border-blue-900/50">
        <span className="text-muted-foreground font-medium">Image Store:</span>
        <span className="font-semibold text-foreground">{imageMode}</span>
      </div>
    </div>
  ) : null;

  const features = [
    "Document embeddings and vector representations",
    "Search indices for visual content retrieval",
    "Supports image storage via MinIO or inline encoding",
  ];

  return (
    <StatusCard
      title="Qdrant Collection"
      description="Vector Database"
      icon={Database}
      iconColor="text-blue-600"
      iconBg="bg-blue-100"
      accentColor="blue"
      isLoading={isLoading}
      status={status}
      exists={status?.exists}
      details={details}
      features={features}
    />
  );
}
