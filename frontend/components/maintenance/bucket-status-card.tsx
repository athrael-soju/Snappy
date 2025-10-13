import { Server } from "lucide-react";
import { StatusCard } from "./status-card";
import type { BucketStatus } from "./types";

interface BucketStatusCardProps {
  status: BucketStatus | null;
  isLoading: boolean;
}

export function BucketStatusCard({ status, isLoading }: BucketStatusCardProps) {
  const isDisabled = !!status?.disabled;
  const details = status ? (
    isDisabled ? (
      <div className="space-y-2 text-sm">
        <div className="rounded border border-blue-200 bg-blue-50 p-3 text-blue-700 dark:border-blue-900/60 dark:bg-blue-900/40 dark:text-blue-200">
          MinIO storage is disabled. Page images are stored inline with Qdrant payloads.
        </div>
      </div>
    ) : (
      <div className="space-y-2 text-sm">
        <div className="flex justify-between items-center p-2 bg-orange-50 dark:bg-orange-950/40 rounded border border-orange-100 dark:border-orange-900/50">
          <span className="text-muted-foreground font-medium">Bucket Name:</span>
          <span className="font-semibold text-foreground">{status.name}</span>
        </div>
        <div className="flex justify-between items-center p-2 bg-orange-50 dark:bg-orange-950/40 rounded border border-orange-100 dark:border-orange-900/50">
          <span className="text-muted-foreground font-medium">Object Count:</span>
          <span className="font-semibold text-foreground">{status.object_count.toLocaleString()}</span>
        </div>
      </div>
    )
  ) : null;

  const features = isDisabled
    ? [
        "Rendered page images are embedded directly in Qdrant payloads",
        "No external object storage service required",
        "Ideal for lightweight or local deployments",
      ]
    : [
        "Original uploaded documents and images",
        "Processed file thumbnails and previews",
        "File metadata and storage organization",
      ];

  return (
    <StatusCard
      title="MinIO Bucket"
      description="Object Storage"
      icon={Server}
      iconColor="text-orange-600"
      iconBg="bg-orange-100"
      accentColor="orange"
      isLoading={isLoading}
      status={status}
      exists={status?.exists}
      details={details}
      features={features}
    />
  );
}
