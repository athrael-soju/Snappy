"use client";

import { useCallback, useEffect, useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Loader2, Flame, Image as ImageIcon } from "lucide-react";
import { baseUrl } from "@/lib/api/client";
import { cn } from "@/lib/utils";

export type PageImageDialogProps = {
  open: boolean;
  src: string;
  alt?: string;
  query?: string;
  onOpenChange: (open: boolean) => void;
};

export default function PageImageDialog({
  open,
  src,
  alt,
  query,
  onOpenChange,
}: PageImageDialogProps) {
  const [showHeatmap, setShowHeatmap] = useState(false);
  const [heatmapUrl, setHeatmapUrl] = useState<string | null>(null);
  const [heatmapLoading, setHeatmapLoading] = useState(false);
  const [heatmapError, setHeatmapError] = useState<string | null>(null);

  // Reset state when dialog closes
  useEffect(() => {
    if (!open) {
      setShowHeatmap(false);
      setHeatmapUrl(null);
      setHeatmapError(null);
    }
  }, [open]);

  // Fetch heatmap when toggle is enabled
  const fetchHeatmap = useCallback(async () => {
    if (!src || !query) {
      setHeatmapError("Query is required to generate heatmap");
      return;
    }

    setHeatmapLoading(true);
    setHeatmapError(null);

    try {
      const params = new URLSearchParams({
        image_url: src,
        query: query,
        alpha: "0.5",
      });

      const response = await fetch(`${baseUrl}/heatmap?${params.toString()}`);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Failed to generate heatmap: ${response.status}`);
      }

      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      setHeatmapUrl(url);
    } catch (error) {
      console.error("Heatmap fetch error:", error);
      setHeatmapError(error instanceof Error ? error.message : "Failed to generate heatmap");
      setShowHeatmap(false);
    } finally {
      setHeatmapLoading(false);
    }
  }, [src, query]);

  // Handle heatmap toggle
  const handleHeatmapToggle = useCallback(
    (enabled: boolean) => {
      setShowHeatmap(enabled);
      if (enabled && !heatmapUrl) {
        fetchHeatmap();
      }
    },
    [heatmapUrl, fetchHeatmap]
  );

  // Cleanup blob URL on unmount
  useEffect(() => {
    return () => {
      if (heatmapUrl) {
        URL.revokeObjectURL(heatmapUrl);
      }
    };
  }, [heatmapUrl]);

  const displaySrc = showHeatmap && heatmapUrl ? heatmapUrl : src;
  const hasQuery = Boolean(query?.trim());

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="!max-w-fit sm:!max-w-fit !max-h-[98vh] p-0 overflow-hidden flex flex-col w-auto">
        <DialogHeader className="sr-only">
          <DialogTitle>{alt || "Document Page"}</DialogTitle>
          <DialogDescription>
            {showHeatmap
              ? "Attention heatmap showing query relevance"
              : "Full size document page view"}
          </DialogDescription>
        </DialogHeader>

        {/* Heatmap toggle control */}
        {hasQuery && (
          <div className="flex items-center justify-between gap-4 border-b px-4 py-3 bg-muted/30">
            <div className="flex items-center gap-2">
              {showHeatmap ? (
                <Flame className="size-icon-sm text-orange-500" />
              ) : (
                <ImageIcon className="size-icon-sm text-muted-foreground" />
              )}
              <Label
                htmlFor="heatmap-toggle"
                className={cn(
                  "text-body-sm cursor-pointer select-none",
                  showHeatmap ? "text-orange-600 font-medium" : "text-muted-foreground"
                )}
              >
                {showHeatmap ? "Showing Attention Heatmap" : "Show Attention Heatmap"}
              </Label>
            </div>
            <div className="flex items-center gap-2">
              {heatmapLoading && (
                <Loader2 className="size-icon-sm animate-spin text-muted-foreground" />
              )}
              <Switch
                id="heatmap-toggle"
                checked={showHeatmap}
                onCheckedChange={handleHeatmapToggle}
                disabled={heatmapLoading}
              />
            </div>
          </div>
        )}

        {/* Image display */}
        <div className="relative flex items-center justify-center bg-background p-0">
          {heatmapLoading && showHeatmap ? (
            <div className="flex flex-col items-center justify-center gap-3 p-12">
              <Loader2 className="size-8 animate-spin text-primary" />
              <p className="text-body-sm text-muted-foreground">Generating attention heatmap...</p>
            </div>
          ) : displaySrc ? (
            <img
              src={displaySrc}
              alt={showHeatmap ? `Attention heatmap for: ${alt || "document"}` : alt || "Full image"}
              className="max-h-[85vh] max-w-[95vw] h-auto w-auto object-contain"
            />
          ) : null}
        </div>

        {/* Error message */}
        {heatmapError && (
          <div className="border-t px-4 py-2 bg-destructive/10">
            <p className="text-center text-body-xs text-destructive">{heatmapError}</p>
          </div>
        )}

        {/* Caption */}
        {alt && (
          <div className="border-t px-4 py-3">
            <p className="text-center text-body-xs text-muted-foreground line-clamp-2">{alt}</p>
          </div>
        )}

        {/* Heatmap legend */}
        {showHeatmap && heatmapUrl && !heatmapLoading && (
          <div className="border-t px-4 py-2 bg-muted/20">
            <div className="flex items-center justify-center gap-4 text-body-xs text-muted-foreground">
              <span className="flex items-center gap-1.5">
                <span className="inline-block w-3 h-3 rounded-sm bg-blue-500" />
                Low attention
              </span>
              <span className="flex items-center gap-1.5">
                <span className="inline-block w-3 h-3 rounded-sm bg-green-500" />
                Medium
              </span>
              <span className="flex items-center gap-1.5">
                <span className="inline-block w-3 h-3 rounded-sm bg-red-500" />
                High attention
              </span>
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
