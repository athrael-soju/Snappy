import { Database } from "lucide-react";
import { StatusCard } from "./status-card";
import { CollectionStatus } from "@/components/maintenance/types";

interface CollectionStatusCardProps {
  status: CollectionStatus | null;
  isLoading: boolean;
}

export function CollectionStatusCard({ status, isLoading }: CollectionStatusCardProps) {
  const details = status ? (
    <div className="space-y-2 text-sm">
      <div className="flex justify-between items-center p-2 bg-blue-50/50 rounded">
        <span className="text-muted-foreground">Collection Name:</span>
        <span className="font-medium">{status.name}</span>
      </div>
      <div className="flex justify-between items-center p-2 bg-blue-50/50 rounded">
        <span className="text-muted-foreground">Vector Count:</span>
        <span className="font-medium">{status.vector_count.toLocaleString()}</span>
      </div>
      <div className="flex justify-between items-center p-2 bg-blue-50/50 rounded">
        <span className="text-muted-foreground">Unique Files:</span>
        <span className="font-medium">{status.unique_files.toLocaleString()}</span>
      </div>
    </div>
  ) : null;

  const features = [
    "Document embeddings and vector representations",
    "Search indices for visual content retrieval",
    "AI-generated semantic understanding data",
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
