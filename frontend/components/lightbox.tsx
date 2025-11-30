"use client";

import { useEffect, useRef, useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Loader2 } from "lucide-react";
import {
  InterpretabilityHeatmap,
  TokenSelector,
  type InterpretabilityData,
} from "@/components/interpretability-heatmap";
import { generateInterpretabilityMaps } from "@/lib/api/interpretability";

export type ImageLightboxProps = {
  open: boolean;
  src: string;
  alt?: string;
  query?: string;
  onOpenChange: (open: boolean) => void;
};

export default function ImageLightbox({
  open,
  src,
  alt,
  query,
  onOpenChange,
}: ImageLightboxProps) {
  const [showInterpretability, setShowInterpretability] = useState(false);
  const [interpretabilityData, setInterpretabilityData] =
    useState<InterpretabilityData | null>(null);
  const [selectedToken, setSelectedToken] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [imageDimensions, setImageDimensions] = useState({ width: 0, height: 0 });
  const imgRef = useRef<HTMLImageElement>(null);

  // Reset state when dialog opens/closes
  useEffect(() => {
    if (!open) {
      setShowInterpretability(false);
      setInterpretabilityData(null);
      setSelectedToken(null);
      setError(null);
    }
  }, [open]);

  // Load interpretability data when toggle is enabled
  useEffect(() => {
    if (showInterpretability && !interpretabilityData && query && src) {
      setLoading(true);
      setError(null);

      generateInterpretabilityMaps(query, src)
        .then((data) => {
          setInterpretabilityData(data);
          // Auto-select the first token to show the heatmap immediately
          if (data.tokens && data.tokens.length > 0) {
            setSelectedToken(0);
          }
          setLoading(false);

          // Force dimension update when data loads
          // The ResizeObserver might not have fired yet if dimensions haven't changed
          setTimeout(() => {
            const img = imgRef.current;
            if (img && img.clientWidth > 0 && img.clientHeight > 0) {
              setImageDimensions({
                width: img.clientWidth,
                height: img.clientHeight,
              });
            }
          }, 50);
        })
        .catch((err) => {
          setError(`Failed to load interpretability: ${err.message}`);
          setLoading(false);
        });
    }
  }, [showInterpretability, interpretabilityData, query, src]);

  // Track DISPLAYED image dimensions (not natural dimensions)
  useEffect(() => {
    const img = imgRef.current;
    if (!img) return;

    const updateDimensions = () => {
      // Use clientWidth/clientHeight for the DISPLAYED size
      const displayedWidth = img.clientWidth;
      const displayedHeight = img.clientHeight;

      // Only update if we have valid dimensions
      if (displayedWidth > 0 && displayedHeight > 0) {
        setImageDimensions({
          width: displayedWidth,
          height: displayedHeight,
        });
      } else {
        // Retry after a short delay if dimensions aren't ready
        setTimeout(updateDimensions, 100);
      }
    };

    // Update dimensions when image loads and when window resizes
    const resizeObserver = new ResizeObserver(updateDimensions);

    if (img.complete && img.naturalWidth > 0) {
      // Image already loaded, wait a tick for layout
      setTimeout(updateDimensions, 10);
    } else {
      img.addEventListener("load", updateDimensions);
    }

    resizeObserver.observe(img);

    return () => {
      img.removeEventListener("load", updateDimensions);
      resizeObserver.disconnect();
    };
  }, [src]);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="!max-w-fit sm:!max-w-fit !max-h-[95vh] p-0 overflow-hidden flex flex-col w-auto">
        <DialogHeader className="sr-only">
          <DialogTitle>{alt || "Image"}</DialogTitle>
          <DialogDescription>Full size image view</DialogDescription>
        </DialogHeader>

        {query && (
          <div className="border-b px-4 py-3 flex items-start gap-3">
            <div className="flex items-center gap-2 shrink-0">
              <Switch
                id="interpretability-toggle"
                checked={showInterpretability}
                onCheckedChange={setShowInterpretability}
                disabled={loading}
              />
              <Label
                htmlFor="interpretability-toggle"
                className="text-body-sm cursor-pointer whitespace-nowrap"
              >
                Show Heat Map
              </Label>
              {loading && <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />}
            </div>
            {showInterpretability && interpretabilityData && (
              <>
                <div className="h-5 w-px bg-border shrink-0" />
                <div className="flex-1 min-w-0 max-h-16 overflow-y-auto">
                  <TokenSelector
                    tokens={interpretabilityData.tokens}
                    selectedToken={selectedToken}
                    onTokenSelect={setSelectedToken}
                  />
                </div>
              </>
            )}
            {error && (
              <div className="px-3 py-2 bg-destructive/10 border border-destructive/20 rounded-md w-full">
                <p className="text-body-sm text-destructive font-medium">{error}</p>
                <p className="text-body-xs text-destructive/80 mt-1">Check browser console (F12) for details</p>
              </div>
            )}
          </div>
        )}

        <div className="relative flex items-center justify-center bg-background p-0">
          {src ? (
            <>
              <img
                ref={imgRef}
                src={src}
                alt={alt || "Full image"}
                className="max-h-[80vh] max-w-[95vw] h-auto w-auto object-contain"
              />
              {showInterpretability && interpretabilityData && imageDimensions.width > 0 && (
                <InterpretabilityHeatmap
                  data={interpretabilityData}
                  imageWidth={imageDimensions.width}
                  imageHeight={imageDimensions.height}
                  selectedToken={selectedToken ?? undefined}
                />
              )}
            </>
          ) : null}
        </div>


        {alt && (
          <div className="border-t px-4 py-3">
            <p className="text-center text-body-xs text-muted-foreground line-clamp-2">
              {alt}
            </p>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
