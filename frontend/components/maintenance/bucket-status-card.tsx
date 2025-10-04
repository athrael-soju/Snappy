import { Server } from "lucide-react";
import { StatusCard } from "./status-card";
import type { BucketStatus } from "./types";

interface BucketStatusCardProps {
  status: BucketStatus | null;
  isLoading: boolean;
}

export function BucketStatusCard({ status, isLoading }: BucketStatusCardProps) {
  const details = status ? (
    <div className="space-y-2 text-sm">
      <div className="flex justify-between items-center p-2 bg-orange-50/50 rounded">
        <span className="text-muted-foreground">Bucket Name:</span>
        <span className="font-medium">{status.name}</span>
      </div>
      <div className="flex justify-between items-center p-2 bg-orange-50/50 rounded">
        <span className="text-muted-foreground">Object Count:</span>
        <span className="font-medium">{status.object_count.toLocaleString()}</span>
      </div>
    </div>
  ) : null;

  const features = [
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
