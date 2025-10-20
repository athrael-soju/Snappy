"use client";

import { CheckCircle2, AlertCircle, Loader2, RefreshCw, X } from "lucide-react";

import { AppButton } from "@/components/app-button";
import { cn } from "@/lib/utils";
import { InfoTooltip } from "@/components/info-tooltip";

type SystemStatusActionsProps = {
  className?: string;
  isReady: boolean;
  statusLoading: boolean;
  onRefresh: () => void;
  onClose?: () => void;
};

export function SystemStatusActions({
  className,
  isReady,
  statusLoading,
  onRefresh,
  onClose,
}: SystemStatusActionsProps) {
  const StatusIcon = isReady ? CheckCircle2 : AlertCircle;
  const statusLabel = isReady ? "Systems nominal" : "Systems off-nominal";

  const stateStyles = isReady
    ? {
        container:
          "border-emerald-300/60 bg-emerald-400/12 text-emerald-800 dark:border-emerald-300/40 dark:bg-emerald-500/15 dark:text-emerald-100",
        button:
          "border-emerald-300/60 bg-white/80 text-emerald-700 hover:bg-white/95 hover:text-emerald-800 dark:border-emerald-300/40 dark:bg-emerald-400/15 dark:text-emerald-50 dark:hover:bg-emerald-400/25",
        close:
          "text-emerald-700 hover:bg-emerald-500/20 hover:text-emerald-900 dark:text-emerald-100 dark:hover:bg-emerald-400/20",
        iconWrap:
          "bg-emerald-500/15 text-emerald-700 dark:bg-emerald-400/25 dark:text-emerald-50",
        tooltipContent: "",
      }
    : {
        container:
          "border-destructive/60 bg-destructive/12 text-destructive dark:border-destructive/70 dark:bg-destructive/20 dark:text-destructive-foreground",
        button:
          "border-destructive/70 bg-white/85 text-destructive hover:bg-white hover:text-destructive dark:border-destructive/70 dark:bg-transparent dark:text-destructive-foreground dark:hover:bg-destructive/20",
        close:
          "text-destructive hover:bg-destructive/15 hover:text-destructive-foreground dark:text-destructive-foreground dark:hover:bg-destructive/25",
        iconWrap:
          "bg-destructive/18 text-destructive dark:bg-destructive/30 dark:text-destructive-foreground",
        tooltipContent:
          "rounded-[var(--radius-card)] border border-destructive/40 bg-white px-4 py-3 text-left text-destructive shadow-[0_18px_38px_-28px_rgba(199,44,72,0.55)] dark:bg-vultr-midnight dark:text-destructive-foreground dark:border-destructive/50",
      };

  return (
    <div
      className={cn(
        "inline-flex items-center gap-3 rounded-[var(--radius-card)] border px-4 py-3 text-body-xs font-medium shadow-[0_20px_48px_-34px_rgba(9,25,74,0.6)] backdrop-blur-md transition-colors md:text-body-sm",
        stateStyles.container,
        className,
      )}
    >
      <div className="inline-flex items-center gap-2 uppercase tracking-wide">
        {statusLoading ? (
          <Loader2 className="size-icon-2xs animate-spin text-current" />
        ) : !isReady ? (
          <InfoTooltip
            trigger={
              <span
                className={cn(
                  "inline-flex size-6 items-center justify-center rounded-full shadow-sm transition",
                  stateStyles.iconWrap,
                  "hover:bg-destructive/25 dark:hover:bg-destructive/35",
                )}
              >
                <StatusIcon className="size-icon-xs" />
              </span>
            }
            title="Bring Morty back to nominal"
            description="Initialize storage or delete and re-initialize Qdrant and MinIO from the Maintenance page."
            contentClassName={cn(
              "max-w-sm",
              stateStyles.tooltipContent,
            )}
            side="top"
          />
        ) : (
          <span
            className={cn(
              "inline-flex size-6 items-center justify-center rounded-full shadow-sm",
              stateStyles.iconWrap,
            )}
          >
            <StatusIcon className="size-icon-xs" />
          </span>
        )}
        <span className="font-semibold">{statusLabel}</span>
      </div>
      <AppButton
        type="button"
        onClick={onRefresh}
        disabled={statusLoading}
        size="xs"
        variant="outline"
        className={cn(
          "h-9 rounded-[var(--radius-button)] px-3 text-body-xs font-medium transition-colors md:text-body-sm",
          stateStyles.button,
          statusLoading ? "cursor-wait" : "",
        )}
      >
        {statusLoading ? (
          <>
            <Loader2 className="size-icon-2xs animate-spin text-current" />
            Refreshing…
          </>
        ) : (
          <>
            <RefreshCw className="size-icon-2xs text-current" />
          </>
        )}
      </AppButton>
      {onClose ? (
        <AppButton
          type="button"
          onClick={onClose}
          size="icon-sm"
          variant="ghost"
          className={cn(
            "rounded-full transition-colors",
            stateStyles.close,
          )}
          aria-label="Dismiss system status panel"
        >
          <X className="size-icon-2xs" />
        </AppButton>
      ) : null}
    </div>
  );
}
