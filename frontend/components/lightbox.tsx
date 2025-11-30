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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { Loader2 } from "lucide-react";
import {
  InterpretabilityHeatmap,
  type InterpretabilityData,
  type ColorScale,
  type NormalizationStrategy,
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
  const [colorScale, setColorScale] = useState<ColorScale>(() => {
    const stored = localStorage.getItem("interpretability-color-scale");
    return (stored as ColorScale) || "YlOrRd";
  });
  const [normalizationStrategy, setNormalizationStrategy] = useState<NormalizationStrategy>(() => {
    const stored = localStorage.getItem("interpretability-normalization-strategy");
    return (stored as NormalizationStrategy) || "percentile";
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [imageDimensions, setImageDimensions] = useState({ width: 0, height: 0 });
  const imgRef = useRef<HTMLImageElement>(null);

  // Save color scale to localStorage
  useEffect(() => {
    localStorage.setItem("interpretability-color-scale", colorScale);
  }, [colorScale]);

  // Save normalization strategy to localStorage
  useEffect(() => {
    localStorage.setItem("interpretability-normalization-strategy", normalizationStrategy);
  }, [normalizationStrategy]);

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
      <DialogContent className="!max-w-fit sm:!max-w-fit !max-h-[95vh] p-0 overflow-hidden flex flex-col w-auto" showCloseButton={false}>
        <DialogHeader className="sr-only">
          <DialogTitle>{alt || "Image"}</DialogTitle>
          <DialogDescription>Full size image view</DialogDescription>
        </DialogHeader>

        {query && (
          <TooltipProvider>
            <div className="relative border-b px-4 flex items-center gap-3 h-12 overflow-hidden">
              <div className="flex items-center gap-2 shrink-0 h-8">
                <Tooltip>
                  <TooltipTrigger asChild>
                    <div className="flex items-center h-8">
                      <Switch
                        id="interpretability-toggle"
                        checked={showInterpretability}
                        onCheckedChange={setShowInterpretability}
                        disabled={loading}
                      />
                    </div>
                  </TooltipTrigger>
                  <TooltipContent>
                    <p>Show heat map overlay</p>
                  </TooltipContent>
                </Tooltip>
                {loading && <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />}
              </div>
              {showInterpretability && (
                <>
                  <div className="h-8 w-px bg-border shrink-0" />
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <div className="flex items-center flex-1 h-8">
                        <Select value={colorScale} onValueChange={(value) => setColorScale(value as ColorScale)}>
                          <SelectTrigger id="color-scale" className="h-8 w-full text-body-xs">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="YlOrRd">Yellow-Red</SelectItem>
                            <SelectItem value="YlGnBu">Yellow-Blue</SelectItem>
                            <SelectItem value="Reds">Reds</SelectItem>
                            <SelectItem value="Blues">Blues</SelectItem>
                            <SelectItem value="Oranges">Oranges</SelectItem>
                            <SelectItem value="Purples">Purples</SelectItem>
                            <SelectItem value="Spectral">Spectral</SelectItem>
                            <SelectItem value="RdYlBu">Red-Blue</SelectItem>
                            <SelectItem value="RdBu">Red-Blue (alt)</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                    </TooltipTrigger>
                    <TooltipContent>
                      <p>Color scale for heat map</p>
                    </TooltipContent>
                  </Tooltip>
                  <div className="h-8 w-px bg-border shrink-0" />
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <div className="flex items-center flex-1 h-8">
                        <Select value={normalizationStrategy} onValueChange={(value) => setNormalizationStrategy(value as NormalizationStrategy)}>
                          <SelectTrigger id="normalization-strategy" className="h-8 w-full text-body-xs">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="percentile">Percentile</SelectItem>
                            <SelectItem value="minmax">Min-Max</SelectItem>
                            <SelectItem value="robust">Robust</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                    </TooltipTrigger>
                    <TooltipContent>
                      <p>Normalization strategy</p>
                    </TooltipContent>
                  </Tooltip>
                </>
              )}
              {showInterpretability && interpretabilityData && (
                <>
                  <div className="h-8 w-px bg-border shrink-0" />
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <div className="flex items-center flex-1 h-8">
                        <Select
                          value={selectedToken !== null ? selectedToken.toString() : undefined}
                          onValueChange={(value) => setSelectedToken(parseInt(value))}
                        >
                          <SelectTrigger id="token-selector" className="h-8 w-full text-body-xs">
                            <SelectValue placeholder="Select token" />
                          </SelectTrigger>
                          <SelectContent>
                            {interpretabilityData.tokens.map((token, idx) => (
                              <SelectItem key={idx} value={idx.toString()}>
                                {token}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                    </TooltipTrigger>
                    <TooltipContent>
                      <p>Select token to visualize</p>
                    </TooltipContent>
                  </Tooltip>
                </>
              )}
              {error && (
                <div className="absolute top-full left-0 right-0 z-10 px-4 py-2 bg-destructive/10 border-b border-destructive/20">
                  <p className="text-body-sm text-destructive font-medium">{error}</p>
                  <p className="text-body-xs text-destructive/80 mt-1">Check browser console (F12) for details</p>
                </div>
              )}
            </div>
          </TooltipProvider>
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
                  colorScale={colorScale}
                  normalizationStrategy={normalizationStrategy}
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
