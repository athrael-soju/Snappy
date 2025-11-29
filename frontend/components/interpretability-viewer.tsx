"use client";

import { useState, useCallback, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { AppButton } from "@/components/app-button";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Slider } from "@/components/ui/slider";
import {
  Loader2,
  Eye,
  EyeOff,
  Sparkles,
  ChevronLeft,
  ChevronRight,
  RefreshCw,
  Layers,
} from "lucide-react";
import { logger } from "@/lib/utils/logger";
import { InterpretabilityService } from "@/lib/api/generated";
import type { SimilarityMapResponse, TokenInfo } from "@/lib/api/generated";

export interface InterpretabilityViewerProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  imageUrl: string;
  query: string;
  title?: string;
}

export default function InterpretabilityViewer({
  open,
  onOpenChange,
  imageUrl,
  query,
  title,
}: InterpretabilityViewerProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<SimilarityMapResponse | null>(null);
  const [selectedTokenIndex, setSelectedTokenIndex] = useState<number | null>(null);
  const [showOriginal, setShowOriginal] = useState(true);
  const [alpha, setAlpha] = useState(0.5);
  const [showFiltered, setShowFiltered] = useState(false);

  // Filter tokens based on showFiltered setting
  const displayTokens = useMemo(() => {
    if (!data) return [];
    return data.tokens.filter(t => showFiltered || !t.should_filter);
  }, [data, showFiltered]);

  // Get current similarity map
  const currentMap = useMemo(() => {
    if (!data || selectedTokenIndex === null) return null;
    return data.similarity_maps.find(m => m.token_index === selectedTokenIndex);
  }, [data, selectedTokenIndex]);

  // Display image source
  const displaySrc = useMemo(() => {
    if (showOriginal || !currentMap) return imageUrl;
    return `data:image/png;base64,${currentMap.similarity_map_base64}`;
  }, [showOriginal, currentMap, imageUrl]);

  const fetchSimilarityMaps = useCallback(async (tokenIndices?: number[]) => {
    setLoading(true);
    setError(null);

    try {
      const result = await InterpretabilityService.generateSimilarityMapInterpretabilitySimilarityMapPost({
        image_url: imageUrl,
        query: query,
        selected_tokens: tokenIndices ?? null,
        alpha: alpha,
      });

      setData(result);

      // Auto-select first non-filtered token if none selected
      if (selectedTokenIndex === null && result.similarity_maps.length > 0) {
        setSelectedTokenIndex(result.similarity_maps[0].token_index);
        setShowOriginal(false);
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to generate similarity maps";
      logger.error("Similarity map generation failed", { error: err });
      setError(message);
    } finally {
      setLoading(false);
    }
  }, [imageUrl, query, alpha, selectedTokenIndex]);

  // Generate maps when dialog opens
  const handleOpenChange = useCallback((isOpen: boolean) => {
    if (isOpen && !data && !loading) {
      fetchSimilarityMaps();
    }
    onOpenChange(isOpen);
  }, [data, loading, fetchSimilarityMaps, onOpenChange]);

  // Regenerate with different alpha
  const handleAlphaChange = useCallback((value: number[]) => {
    setAlpha(value[0]);
  }, []);

  const handleRegenerateWithAlpha = useCallback(() => {
    if (data) {
      // Get token indices that have maps
      const tokenIndices = data.similarity_maps.map(m => m.token_index);
      fetchSimilarityMaps(tokenIndices);
    }
  }, [data, fetchSimilarityMaps]);

  // Navigate between tokens
  const handlePrevToken = useCallback(() => {
    if (!data || selectedTokenIndex === null) return;
    const currentIdx = displayTokens.findIndex(t => t.index === selectedTokenIndex);
    if (currentIdx > 0) {
      const prevToken = displayTokens[currentIdx - 1];
      // Check if we have a map for this token
      const hasMap = data.similarity_maps.some(m => m.token_index === prevToken.index);
      if (hasMap) {
        setSelectedTokenIndex(prevToken.index);
        setShowOriginal(false);
      }
    }
  }, [data, selectedTokenIndex, displayTokens]);

  const handleNextToken = useCallback(() => {
    if (!data || selectedTokenIndex === null) return;
    const currentIdx = displayTokens.findIndex(t => t.index === selectedTokenIndex);
    if (currentIdx < displayTokens.length - 1) {
      const nextToken = displayTokens[currentIdx + 1];
      // Check if we have a map for this token
      const hasMap = data.similarity_maps.some(m => m.token_index === nextToken.index);
      if (hasMap) {
        setSelectedTokenIndex(nextToken.index);
        setShowOriginal(false);
      }
    }
  }, [data, selectedTokenIndex, displayTokens]);

  // Generate map for a specific token
  const handleTokenClick = useCallback((tokenIndex: number) => {
    const hasMap = data?.similarity_maps.some(m => m.token_index === tokenIndex);
    if (hasMap) {
      setSelectedTokenIndex(tokenIndex);
      setShowOriginal(false);
    } else {
      // Need to generate map for this token
      fetchSimilarityMaps([tokenIndex]);
      setSelectedTokenIndex(tokenIndex);
    }
  }, [data, fetchSimilarityMaps]);

  const selectedToken = useMemo(() => {
    if (!data || selectedTokenIndex === null) return null;
    return data.tokens.find(t => t.index === selectedTokenIndex);
  }, [data, selectedTokenIndex]);

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="!max-w-[95vw] !max-h-[98vh] p-0 overflow-hidden flex flex-col w-auto sm:!max-w-6xl">
        <DialogHeader className="px-4 pt-4 pb-2 border-b shrink-0">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Sparkles className="size-icon-sm text-primary" />
              <DialogTitle className="text-body font-bold">
                Interpretability Map
              </DialogTitle>
            </div>
            <Badge variant="secondary" className="text-body-xs">
              Query: &quot;{query.length > 30 ? query.slice(0, 30) + "..." : query}&quot;
            </Badge>
          </div>
          <DialogDescription className="sr-only">
            Visual similarity maps showing which parts of the image match each query token
          </DialogDescription>
        </DialogHeader>

        <div className="flex flex-1 min-h-0 overflow-hidden">
          {/* Main image area */}
          <div className="flex-1 flex flex-col min-w-0 p-4">
            {/* Image container */}
            <div className="flex-1 relative flex items-center justify-center bg-muted/30 rounded-lg overflow-hidden min-h-0">
              <AnimatePresence mode="wait">
                {loading ? (
                  <motion.div
                    key="loading"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="flex flex-col items-center gap-3"
                  >
                    <Loader2 className="size-icon-xl animate-spin text-primary" />
                    <p className="text-body-sm text-muted-foreground">
                      Generating similarity maps...
                    </p>
                  </motion.div>
                ) : error ? (
                  <motion.div
                    key="error"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="flex flex-col items-center gap-3 p-4"
                  >
                    <p className="text-body-sm text-destructive text-center">{error}</p>
                    <AppButton
                      variant="outline"
                      size="sm"
                      onClick={() => fetchSimilarityMaps()}
                    >
                      <RefreshCw className="size-icon-xs mr-1" />
                      Retry
                    </AppButton>
                  </motion.div>
                ) : (
                  <motion.img
                    key={displaySrc}
                    src={displaySrc}
                    alt={title || "Document page"}
                    className="max-h-full max-w-full h-auto w-auto object-contain"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ duration: 0.2 }}
                  />
                )}
              </AnimatePresence>
            </div>

            {/* Controls */}
            <div className="shrink-0 mt-3 flex items-center justify-between gap-4">
              <div className="flex items-center gap-2">
                <AppButton
                  variant={showOriginal ? "default" : "outline"}
                  size="sm"
                  onClick={() => setShowOriginal(true)}
                  disabled={loading}
                >
                  <Eye className="size-icon-xs mr-1" />
                  Original
                </AppButton>
                <AppButton
                  variant={!showOriginal && currentMap ? "default" : "outline"}
                  size="sm"
                  onClick={() => currentMap && setShowOriginal(false)}
                  disabled={loading || !currentMap}
                >
                  <Layers className="size-icon-xs mr-1" />
                  Similarity Map
                </AppButton>
              </div>

              <div className="flex items-center gap-2">
                <AppButton
                  variant="ghost"
                  size="icon-sm"
                  onClick={handlePrevToken}
                  disabled={loading || !data || selectedTokenIndex === null}
                >
                  <ChevronLeft className="size-icon-sm" />
                </AppButton>
                {selectedToken && (
                  <Badge variant="secondary" className="min-w-16 justify-center">
                    {selectedToken.token}
                  </Badge>
                )}
                <AppButton
                  variant="ghost"
                  size="icon-sm"
                  onClick={handleNextToken}
                  disabled={loading || !data || selectedTokenIndex === null}
                >
                  <ChevronRight className="size-icon-sm" />
                </AppButton>
              </div>
            </div>
          </div>

          {/* Side panel - Token list */}
          <div className="w-64 border-l bg-card/50 flex flex-col shrink-0">
            <div className="p-3 border-b shrink-0">
              <h4 className="text-body-sm font-semibold mb-2">Query Tokens</h4>
              <label className="flex items-center gap-2 text-body-xs text-muted-foreground">
                <input
                  type="checkbox"
                  checked={showFiltered}
                  onChange={(e) => setShowFiltered(e.target.checked)}
                  className="rounded"
                />
                Show filtered tokens
              </label>
            </div>

            <ScrollArea className="flex-1">
              <div className="p-2 space-y-1">
                {data?.tokens.map((token) => {
                  const isFiltered = token.should_filter;
                  const isHidden = isFiltered && !showFiltered;
                  const isSelected = token.index === selectedTokenIndex;
                  const hasMap = data.similarity_maps.some(m => m.token_index === token.index);

                  if (isHidden) return null;

                  return (
                    <button
                      key={token.index}
                      onClick={() => handleTokenClick(token.index)}
                      disabled={loading}
                      className={`w-full text-left px-3 py-2 rounded-lg text-body-sm transition-colors ${
                        isSelected
                          ? "bg-primary text-primary-foreground"
                          : isFiltered
                          ? "bg-muted/50 text-muted-foreground hover:bg-muted"
                          : hasMap
                          ? "bg-secondary hover:bg-secondary/80"
                          : "hover:bg-muted"
                      }`}
                    >
                      <span className="font-mono">{token.token}</span>
                      {isFiltered && (
                        <EyeOff className="size-icon-3xs inline ml-1 opacity-50" />
                      )}
                      {hasMap && !isSelected && (
                        <Sparkles className="size-icon-3xs inline ml-1 text-primary" />
                      )}
                    </button>
                  );
                })}
              </div>
            </ScrollArea>

            {/* Alpha control */}
            <div className="p-3 border-t shrink-0">
              <label className="text-body-xs font-medium text-muted-foreground mb-2 block">
                Overlay Opacity: {Math.round(alpha * 100)}%
              </label>
              <div className="flex items-center gap-2">
                <Slider
                  value={[alpha]}
                  onValueChange={handleAlphaChange}
                  min={0}
                  max={1}
                  step={0.1}
                  className="flex-1"
                />
                <AppButton
                  variant="ghost"
                  size="icon-sm"
                  onClick={handleRegenerateWithAlpha}
                  disabled={loading || !data}
                  title="Regenerate with new opacity"
                >
                  <RefreshCw className="size-icon-xs" />
                </AppButton>
              </div>
            </div>
          </div>
        </div>

        {title && (
          <div className="border-t px-4 py-2 shrink-0">
            <p className="text-center text-body-xs text-muted-foreground line-clamp-1">
              {title}
            </p>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
