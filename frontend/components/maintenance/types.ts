import { LucideIcon } from "lucide-react";

export type ActionType = "q" | "m" | "all";

export interface CollectionStatus {
  name: string;
  exists: boolean;
  vector_count: number;
  unique_files: number;
  error: string | null;
  embedded?: boolean;
  image_store_mode?: "inline" | "minio" | string;
}

export interface BucketStatus {
  name: string;
  exists: boolean;
  object_count: number;
  error: string | null;
  disabled?: boolean;
}

export interface SystemStatus {
  collection: CollectionStatus;
  bucket: BucketStatus;
}

export interface MaintenanceAction {
  id: ActionType;
  title: string;
  description: string;
  detailedDescription: string;
  icon: LucideIcon;
  color: string;
  bgColor: string;
  borderColor: string;
  buttonVariant: "destructive" | "default" | "outline";
  confirmTitle: string;
  confirmMsg: string;
  successMsg: string;
  severity: "critical" | "normal";
}

export interface LoadingState {
  q: boolean;
  m: boolean;
  all: boolean;
}
