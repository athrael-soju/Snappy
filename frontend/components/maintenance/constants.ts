import { Trash2 } from "lucide-react";
import type { MaintenanceAction } from "./types";

export const MAINTENANCE_ACTIONS: MaintenanceAction[] = [
  {
    id: "all",
    title: "Data Reset",
    description: "Removes all data from both systems",
    detailedDescription: "This will delete all documents, embeddings, and images. The system will return to its initial empty state.",
    icon: Trash2,
    color: "text-red-600",
    bgColor: "bg-red-500/10",
    borderColor: "border-red-300",
    buttonVariant: "destructive",
    confirmTitle: "Data Reset?",
    confirmMsg: "⚠️ DANGER: This will permanently delete ALL data from both Qdrant and MinIO. This includes all documents, embeddings, images, and search indices. This action cannot be undone and will reset the entire system to its initial state.",
    successMsg: "System completely reset",
    severity: "critical"
  }
];
