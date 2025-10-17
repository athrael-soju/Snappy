"use client";

import { ChangeEvent, FormEvent, useMemo, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import "@/lib/api/client";
import Image from "next/image";
import { Search, Loader2, X, AlertCircle, Sparkles, ArrowRight, FileText, Clock } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { RetrievalService } from "@/lib/api/generated";
import { parseSearchResults } from "@/lib/api/runtime";
import { useSearchStore } from "@/lib/hooks/use-search-store";
import { useSystemStatus } from "@/stores/app-store";
import ImageLightbox from "@/components/lightbox";

const suggestedQueries = [
  "Show recent upload summaries",
  "Find diagrams about the architecture",
  "Which contracts mention service levels?",
];

export default function SearchPage() {
  const {
    query,
    setQuery,
    results,
    hasSearched,
    searchDurationMs,
    k,
    setK,
    topK,
    setTopK,
    reset,
    setResults,
    setHasSearched,
  } = useSearchStore();
  const { isReady } = useSystemStatus();

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lightboxOpen, setLightboxOpen] = useState(false);
  const [lightboxSrc, setLightboxSrc] = useState<string>("");
  const [lightboxAlt, setLightboxAlt] = useState<string | null>(null);

  const truncatedResults = useMemo(() => results.slice(0, topK), [results, topK]);

  const handleNumberChange = (event: ChangeEvent<HTMLInputElement>, setter: (value: number) => void) => {
    const next = Number.parseInt(event.target.value, 10);
    if (!Number.isNaN(next)) {
      setter(next);
    }
  };

  const handleSearch = async (event: FormEvent) => {
    event.preventDefault();
    const trimmed = query.trim();
    if (!trimmed) {
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const start = performance.now();
      const data = await RetrievalService.searchSearchGet(trimmed, k);
      const parsed = parseSearchResults(data);
      setResults(parsed, performance.now() - start);
      setHasSearched(true);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Search failed";
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  const clearResults = () => {
    reset();
    setError(null);
  };

  const handleImageOpen = (url: string, label?: string) => {
    if (!url) return;
    setLightboxSrc(url);
    setLightboxAlt(label ?? null);
    setLightboxOpen(true);
  };

  return (
    <div className="relative flex h-full min-h-full flex-col overflow-hidden">
      <div className="flex h-full flex-1 flex-col overflow-hidden px-4 py-6 sm:px-6 lg:px-8">
        <motion.div 
          className="mx-auto flex h-full w-full max-w-5xl flex-col space-y-4"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, ease: "easeOut" }}
        >
          {/* Header Section */}
          <motion.div 
            className="shrink-0 space-y-2 text-center"
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1, duration: 0.3 }}
          >
            <h1 className="text-xl font-bold tracking-tight sm:text-2xl lg:text-3xl">
              <span className="bg-gradient-to-br from-foreground via-foreground to-foreground/70 bg-clip-text text-transparent">
                Search & Discover
              </span>
              {" "}
              <span className="bg-gradient-to-r from-primary via-chart-4 to-primary bg-clip-text text-transparent">
                Your Documents
              </span>
            </h1>
            
            <p className="mx-auto max-w-2xl text-body-xs leading-relaxed text-muted-foreground">
              Ask questions in natural language and let Snappy surface the most relevant matches instantly.
            </p>
            
            {!isReady && (
              <Badge variant="destructive" className="gap-2 text-body-xs">
                <AlertCircle className="size-icon-3xs" />
                System not ready
              </Badge>
            )}
          </motion.div>

          {/* Search Form */}
          <motion.form 
            onSubmit={handleSearch} 
            className="shrink-0 space-y-3"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2, duration: 0.3 }}
          >
            {/* Search Input with Buttons */}
            <motion.div 
              className="group relative overflow-hidden rounded-2xl border-2 border-border/50 bg-card/30 backdrop-blur-sm transition-all focus-within:border-primary/50 focus-within:shadow-xl focus-within:shadow-primary/10"
              whileHover={{ scale: 1.01 }}
              whileTap={{ scale: 0.99 }}
            >
              <div className="absolute inset-0 bg-gradient-to-br from-primary to-chart-4 opacity-0 transition-opacity group-focus-within:opacity-5" />
              
              <div className="relative flex items-center gap-3 p-3 sm:p-4">
                <Search className="size-icon-md shrink-0 text-muted-foreground group-focus-within:text-primary transition-colors" />
                <input
                  type="text"
                  value={query}
                  onChange={(event) => setQuery(event.target.value)}
                  placeholder="Ask about content, visuals, or document details..."
                  className="flex-1 bg-transparent text-body outline-none placeholder:text-muted-foreground"
                  disabled={!isReady}
                />
                
                {/* Inline Search Button */}
                <div className="flex shrink-0 items-center gap-2">
                  <Button
                    type="submit"
                    size="sm"
                    disabled={loading || !isReady || !query.trim()}
                    className="group h-10 gap-2 rounded-full px-4 shadow-lg shadow-primary/20 transition-all hover:shadow-xl hover:shadow-primary/25 touch-manipulation"
                  >
                    {loading ? (
                      <>
                        <Loader2 className="size-icon-sm animate-spin" />
                        <span className="hidden sm:inline">Searching...</span>
                      </>
                    ) : (
                      <>
                        <Search className="size-icon-sm" />
                        <span className="hidden sm:inline">Search</span>
                      </>
                    )}
                  </Button>
                </div>
              </div>
            </motion.div>

            {/* Settings Grid */}
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              <div className="rounded-xl border border-border/50 bg-card/50 p-3 backdrop-blur-sm">
                <label className="flex flex-col gap-2">
                  <span className="text-body-xs font-medium text-muted-foreground">Neighbors (k)</span>
                  <input
                    type="number"
                    min={1}
                    value={k}
                    onChange={(event) => handleNumberChange(event, setK)}
                    className="rounded-lg border border-border/50 bg-background px-3 py-2 text-body-sm outline-none transition-all focus:border-primary/50 focus:ring-2 focus:ring-primary/20"
                  />
                </label>
              </div>
              <div className="rounded-xl border border-border/50 bg-card/50 p-3 backdrop-blur-sm">
                <label className="flex flex-col gap-2">
                  <span className="text-body-xs font-medium text-muted-foreground">Show top results</span>
                  <input
                    type="number"
                    min={1}
                    value={topK}
                    onChange={(event) => handleNumberChange(event, setTopK)}
                    className="rounded-lg border border-border/50 bg-background px-3 py-2 text-body-sm outline-none transition-all focus:border-primary/50 focus:ring-2 focus:ring-primary/20"
                  />
                </label>
              </div>
              <div className="rounded-xl border border-border/50 bg-card/50 p-3 backdrop-blur-sm">
                <div className="flex flex-col gap-2">
                  <span className="text-body-xs font-medium text-muted-foreground">Search Duration</span>
                  <div className="flex items-center gap-2 rounded-lg border border-border/50 bg-background px-3 py-2 text-body-sm">
                    <Clock className="size-icon-sm text-muted-foreground" />
                    <span className="font-medium">
                      {searchDurationMs !== null ? `${(searchDurationMs / 1000).toFixed(2)}s` : '—'}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* Error Message */}
            <AnimatePresence mode="wait">
              {error && (
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  transition={{ duration: 0.2 }}
                >
                  <div className="flex items-center gap-2 rounded-lg bg-destructive/10 px-4 py-3 text-body-sm font-medium text-destructive">
                    <AlertCircle className="size-icon-sm" />
                    {error}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.form>

          {/* Results Section */}
          <AnimatePresence mode="wait">
            {(hasSearched || loading) && (
              <motion.div 
                className="flex min-h-0 flex-1 flex-col space-y-4"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.3 }}
              >
              {/* Results Header - Stats Only */}
              <div className="flex flex-wrap items-center justify-center gap-3">
                {hasSearched && results.length > topK && (
                  <Badge variant="secondary" className="px-3 py-1 text-body-xs">
                    Showing {truncatedResults.length} of {results.length}
                  </Badge>
                )}
              </div>

              {/* Loading State */}
              <AnimatePresence mode="wait">
                {loading && (
                  <motion.div
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.95 }}
                    transition={{ duration: 0.2 }}
                  >
                    <div className="flex items-center justify-center gap-2 rounded-xl border border-border/50 bg-card/50 p-8 backdrop-blur-sm">
                      <Loader2 className="size-icon-md animate-spin text-primary" />
                      <p className="text-body-sm text-muted-foreground">Searching your documents...</p>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>

              {/* No Results */}
              <AnimatePresence mode="wait">
                {!loading && hasSearched && truncatedResults.length === 0 && (
                  <motion.div
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.95 }}
                    transition={{ duration: 0.3 }}
                  >
                    <div className="rounded-xl border border-border/50 bg-card/50 p-8 text-center backdrop-blur-sm">
                      <AlertCircle className="mx-auto size-icon-3xl text-muted-foreground/50" />
                      <p className="mt-3 text-body-sm font-medium text-foreground">No matches found</p>
                      <p className="mt-1 text-body-xs text-muted-foreground">
                        Try adjusting your query or search parameters
                      </p>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>

              {/* Results List */}
              <AnimatePresence mode="wait">
                {!loading && truncatedResults.length > 0 && (
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -20 }}
                    transition={{ duration: 0.3 }}
                    className="flex min-h-0 flex-1 flex-col"
                  >
                  <div className="flex min-h-0 flex-1 flex-col rounded-xl border border-border/50 bg-card/30 p-3 backdrop-blur-sm">
                  {/* List Header */}
                  <div className="mb-2 flex shrink-0 items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <Sparkles className="size-icon-sm text-primary" />
                      <h3 className="text-body-sm font-bold">
                        {truncatedResults.length} {truncatedResults.length === 1 ? "Result" : "Results"}
                      </h3>
                    </div>
                    <Button
                      type="button"
                      onClick={clearResults}
                      size="sm"
                      variant="ghost"
                      className="h-7 gap-1.5 rounded-full px-2 text-body-xs"
                    >
                      <X className="size-icon-3xs" />
                      Clear
                    </Button>
                  </div>
                  
                  <ScrollArea className="min-h-0 flex-1">
                    <div className="space-y-2 pr-4">
                      {truncatedResults.map((item, index) => {
                    const filename = item.payload?.filename;
                    const pageIndex = item.payload?.pdf_page_index;
                    const displayTitle = filename 
                      ? `${filename}${typeof pageIndex === 'number' ? ` - Page ${pageIndex + 1}` : ''}`
                      : item.label ?? `Result ${index + 1}`;
                    
                        return (
                          <motion.article 
                            key={`${item.label ?? index}-${index}`}
                            onClick={() => {
                              if (item.image_url) {
                                handleImageOpen(item.image_url, displayTitle);
                              }
                            }}
                            className="group relative flex gap-3 overflow-hidden rounded-xl border border-border/50 bg-card/50 p-4 backdrop-blur-sm transition-all hover:border-primary/50 hover:shadow-lg hover:shadow-primary/10 cursor-pointer touch-manipulation"
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            exit={{ opacity: 0, x: 20 }}
                            transition={{ delay: index * 0.05, duration: 0.2 }}
                            whileHover={{ scale: 1.02, x: 4 }}
                            whileTap={{ scale: 0.98 }}
                          >
                        <div className="absolute inset-0 bg-gradient-to-br from-primary to-chart-4 opacity-0 transition-opacity group-hover:opacity-5" />
                        
                        {/* Thumbnail */}
                        {item.image_url ? (
                          <div className="relative h-24 w-24 shrink-0 overflow-hidden rounded-lg border border-border/50 bg-background/50">
                            <Image
                              src={item.image_url}
                              alt={displayTitle}
                              width={96}
                              height={96}
                              className="h-full w-full object-cover"
                              unoptimized
                            />
                          </div>
                        ) : (
                          <div className="flex h-24 w-24 shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-primary to-chart-4">
                            <FileText className="size-icon-xl text-primary-foreground" />
                          </div>
                        )}
                        
                        {/* Content */}
                        <div className="relative flex min-w-0 flex-1 flex-col justify-between">
                          {/* Header */}
                          <div className="space-y-1.5">
                            <h3 className="line-clamp-2 text-body-sm sm:text-body font-bold text-foreground">
                              {displayTitle}
                            </h3>
                            <div className="flex flex-wrap gap-1.5">
                              {typeof item.score === "number" && (
                                <Badge variant="secondary" className="h-auto px-2 py-0.5 text-body-xs font-semibold">
                                  {Math.min(100, item.score > 1 ? item.score : item.score * 100).toFixed(3)}% relevance
                                </Badge>
                              )}
                            </div>
                          </div>
                          </div>
                        </motion.article>
                        );
                      })}
                    </div>
                  </ScrollArea>
                  </div>
                </motion.div>
              )}
              </AnimatePresence>
            </motion.div>
          )}
          </AnimatePresence>
        </motion.div>
      </div>
      <ImageLightbox
        open={lightboxOpen}
        src={lightboxSrc}
        alt={lightboxAlt ?? undefined}
        onOpenChange={(open) => {
          setLightboxOpen(open);
          if (!open) {
            setLightboxSrc("");
            setLightboxAlt(null);
          }
        }}
      />
    </div>
  );
}
