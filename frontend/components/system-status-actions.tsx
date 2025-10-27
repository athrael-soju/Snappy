"use client";

import { useMemo, type ReactNode } from "react";
import Image from "next/image";
import Link from "next/link";
import { AlertCircle, CheckCircle2, Loader2, RefreshCw, X } from "lucide-react";

import { AppButton } from "@/components/app-button";
import type { SystemStatus } from "@/stores/types";
import { cn } from "@/lib/utils";

type Severity = "error" | "warning" | "ok";

type SystemStatusActionsProps = {
  className?: string;
  statusLoading: boolean;
  onRefresh: () => void;
  onClose?: () => void;
  systemStatus?: SystemStatus | null;
};

type StatusContent = {
  title: string;
  description: ReactNode;
};

function formatCount(value: number | undefined | null): string {
  if (value === null || value === undefined) return "0";
  return value.toLocaleString();
}

export function resolveSeverity(status: SystemStatus | null | undefined): Severity {
  if (!status) {
    return "warning";
  }

  const collection = status.collection;
  const bucket = status.bucket;

  const collectionError = collection?.error ?? null;
  const bucketError = bucket?.error ?? null;
  const qdrantDown = Boolean(collectionError && collectionError.toLowerCase().includes("service unavailable"));
  const minioDown = Boolean(bucketError && bucketError.toLowerCase().includes("service unavailable"));
  const requiresBucket = (collection?.image_store_mode ?? "minio") !== "inline";

  if (qdrantDown || (requiresBucket && minioDown)) {
    return "error";
  }

  if (!collection?.exists || (requiresBucket && !bucket?.exists)) {
    return "error";
  }

  const vectorCount = collection?.vector_count ?? 0;
  const objectCount = bucket?.object_count ?? 0;
  const uniqueFileCount =
    typeof collection?.unique_files === "number" ? collection.unique_files : null;

  if (vectorCount === 0) {
    return "warning";
  }

  if (requiresBucket) {
    if (objectCount === 0) {
      return "warning";
    }

    if (uniqueFileCount !== null && objectCount > 0 && objectCount < uniqueFileCount) {
      return "warning";
    }
  }

  return "ok";
}

export function SystemStatusActions({
  className,
  statusLoading,
  onRefresh,
  onClose,
  systemStatus,
}: SystemStatusActionsProps) {
  const severity = resolveSeverity(systemStatus);

  const collection = systemStatus?.collection ?? null;
  const bucket = systemStatus?.bucket ?? null;
  const vectorCount = collection?.vector_count ?? 0;
  const uniqueFiles = collection?.unique_files ?? vectorCount;
  const objectCount = bucket?.object_count ?? 0;

  const content = useMemo<StatusContent>(() => {
    if (!systemStatus) {
      return {
        title: statusLoading ? "Checking Morty's systems" : "Morty status pending",
        description: statusLoading
          ? "Fetching the latest Qdrant and MinIO health information."
          : "Morty has not reported any storage status yet.",
      };
    }

    const collectionError = collection?.error ?? null;
    const bucketError = bucket?.error ?? null;
    const qdrantDown = Boolean(collectionError && collectionError.toLowerCase().includes("service unavailable"));
    const minioDown = Boolean(bucketError && bucketError.toLowerCase().includes("service unavailable"));

    if (severity === "error") {
      if (qdrantDown || minioDown) {
        const downTargets = [qdrantDown ? "Qdrant" : null, minioDown ? "MinIO" : null]
          .filter(Boolean) as string[];
        const summary = downTargets.join(" and ");
        return {
          title: "Vultr systems require attention",
          description: downTargets.length
            ? `${summary} container${downTargets.length > 1 ? "s are" : " is"} not reachable. Start the Docker services, then refresh the status.`
            : "Morty cannot reach the storage services. Start the Qdrant and MinIO containers, then refresh the status.",
        };
      }

      if (!collection?.exists || !bucket?.exists) {
        const missingTargets = [
          !collection?.exists ? "Qdrant collection" : null,
          !bucket?.exists ? "MinIO bucket" : null,
        ].filter(Boolean) as string[];
        const summary = missingTargets.join(" and ");
        return {
          title: "Vultr systems require attention",
          description: (
            <>
              {summary} {missingTargets.length > 1 ? "are" : "is"} not initialized.{" "}
              <Link className="font-semibold text-primary underline-offset-2 hover:underline" href="/maintenance">
                Open Maintenance
              </Link>{" "}
              to run Initialize Storage.
            </>
          ),
        };
      }

      return {
        title: "Vultr systems require attention",
        description: collectionError ?? bucketError ?? "Morty reported a storage error.",
      };
    }

    if (severity === "warning") {
      if (vectorCount === 0 || objectCount === 0) {
        return {
          title: "Morty is partially ready",
          description: (
            <>
              Storage is ready but empty.{" "}
              <Link className="font-semibold text-primary underline-offset-2 hover:underline" href="/upload">
                Upload PDFs
              </Link>{" "}
              so Morty can index them.
            </>
          ),
        };
      }

      if (vectorCount !== objectCount) {
        return {
          title: "Morty is partially ready",
          description: (
            <>
              Morty tracks {formatCount(uniqueFiles)} documents but {formatCount(objectCount)} stored page images.{" "}
              <Link className="font-semibold text-primary underline-offset-2 hover:underline" href="/maintenance">
                Reset all data
              </Link>{" "}
              from the Maintenance console, then re-initialize storage.
            </>
          ),
        };
      }
    }

    return {
      title: "Vultr systems nominal",
      description: (
        <>
          Morty indexed {formatCount(uniqueFiles)} documents with {formatCount(vectorCount)} vectors.{" "}
          Visit{" "}
          <Link className="font-semibold text-primary underline-offset-2 hover:underline" href="/search">
            Search
          </Link>{" "}
          or{" "}
          open{" "}
          <Link className="font-semibold text-primary underline-offset-2 hover:underline" href="/chat">
            Chat
          </Link>{" "}
          to start exploring!
        </>
      ),
    };
  }, [bucket, collection, objectCount, severity, statusLoading, systemStatus, uniqueFiles, vectorCount]);

  const severityIconStyles: Record<Severity, string> = {
    error: "border-destructive/35 bg-destructive/20 text-destructive",
    warning: "border-amber-500/35 bg-amber-500/20 text-amber-600",
    ok: "border-emerald-500/35 bg-emerald-500/20 text-emerald-600",
  };

  const StatusIcon = severity === "ok" ? CheckCircle2 : AlertCircle;

  return (
    <div className={cn("pointer-events-auto flex w-full flex-col items-end gap-2", className)}>
      <div
        className="relative flex max-w-xs flex-col gap-1.5 rounded-2xl border border-black/5 bg-white/95 px-3 py-2 text-left text-slate-800 shadow-md backdrop-blur-md dark:border-white/15 dark:bg-vultr-midnight/95 dark:text-white"
      >
        <div className="flex items-start justify-between gap-2">
          <div className="flex items-start gap-2">
            <span
              className={cn(
                "inline-flex size-6 items-center justify-center rounded-full border text-[11px] transition-colors",
                severityIconStyles[severity],
              )}
            >
              {statusLoading ? (
                <Loader2 className="size-icon-xs animate-spin" />
              ) : (
                <StatusIcon className="size-icon-xs" />
              )}
            </span>
            <div className="flex-1 space-y-0.5">
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-600 dark:text-white/70">
                {content.title}
              </p>
              <p className="text-[12px] leading-snug text-slate-600/80 dark:text-white/70">
                {content.description}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-1">
            <AppButton
              type="button"
              onClick={onRefresh}
              disabled={statusLoading}
              size="icon-sm"
              variant="ghost"
              className="size-7 rounded-full border border-black/10 text-slate-600 hover:bg-black/5 dark:border-white/20 dark:text-white/80 dark:hover:bg-white/10"
              aria-label="Refresh system status"
            >
              {statusLoading ? (
                <Loader2 className="size-icon-xs animate-spin" />
              ) : (
                <RefreshCw className="size-icon-xs" />
              )}
            </AppButton>
            {onClose ? (
              <AppButton
                type="button"
                onClick={onClose}
                size="icon-sm"
                variant="ghost"
                className="size-7 rounded-full border border-black/10 text-slate-600 hover:bg-black/5 dark:border-white/20 dark:text-white/80 dark:hover:bg-white/10"
                aria-label="Hide system status"
              >
                <X className="size-icon-xs" />
              </AppButton>
            ) : null}
          </div>
        </div>
      </div>

      <div className="relative h-[70px] w-[70px]">
        <Image
          src="/vultr/morty/engi_morty_nobg.png"
          alt="Engineer Morty"
          fill
          className="object-contain drop-shadow-2xl"
          priority={false}
        />
        <div
          className="absolute inset-0 -z-10 rounded-full bg-white/30 blur-2xl dark:bg-emerald-500/25"
          aria-hidden="true"
        />
      </div>
    </div>
  );
}
