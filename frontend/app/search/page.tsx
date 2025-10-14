"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import Image from "next/image";
import { AnimatePresence, motion } from "framer-motion";
import { Search as SearchIcon, AlertCircle, ImageIcon } from "lucide-react";

import { parseSearchResults, type SearchItem } from "@/lib/api/runtime";
import { RetrievalService, ApiError, MaintenanceService } from "@/lib/api/generated";
import "@/lib/api/client";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import SearchBar from "@/components/search/SearchBar";
import { PageHeader } from "@/components/page-header";
import ImageLightbox from "@/components/lightbox";
import { useSearchStore, useSystemStatus } from "@/stores/app-store";
import { SystemStatusWarning } from "@/components/upload";
import { toast } from "@/components/ui/sonner";

const STORAGE_KEY = "snappy-recent-searches";
const EXAMPLE_QUERIES = [
  "Show me slides with sales targets",
  "Find purchase orders with handwritten notes",
  "Where do we mention pricing tables?",
  "Images of dashboards from Q3 reports",
] as const;

const fadeIn = {
  initial: { opacity: 0, y: 12 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.3 },
};

export default function SearchPage() {
  const {
    query,
    setQuery,
    results,
    setResults,
    hasSearched,
    setHasSearched,
    searchDurationMs,
    k,
    setK,
    topK,
    setTopK,
    reset,
  } = useSearchStore();
  const { setStatus, isReady } = useSystemStatus();

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [recentSearches, setRecentSearches] = useState<string[]>([]);
  const [lightboxOpen, setLightboxOpen] = useState(false);
  const [lightboxSrc, setLightboxSrc] = useState("");
  const [lightboxAlt, setLightboxAlt] = useState<string | undefined>(undefined);
  const [statusLoading, setStatusLoading] = useState(false);

  const inputRef = useRef<HTMLInputElement>(null!);
  const hasResults = hasSearched && results.length > 0;

  const loadSystemStatus = useCallback(async () => {
    setStatusLoading(true);
    try {
      const status = await MaintenanceService.getStatusStatusGet();
      setStatus({ ...status, lastChecked: Date.now() });
    } catch (err) {
      console.error("Failed to fetch system status", err);
    } finally {
      setStatusLoading(false);
    }
  }, [setStatus]);

  useEffect(() => {
    loadSystemStatus();
    window.addEventListener("systemStatusChanged", loadSystemStatus);
    return () => window.removeEventListener("systemStatusChanged", loadSystemStatus);
  }, [loadSystemStatus]);

  useEffect(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) {
        const parsed = JSON.parse(saved) as string[];
        setRecentSearches(Array.isArray(parsed) ? parsed.slice(0, 9) : []);
      }
    } catch {
      setRecentSearches([]);
    }
  }, []);

  const persistRecentSearches = useCallback((queries: string[]) => {
    setRecentSearches(queries);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(queries));
  }, []);

  const addToRecentSearches = useCallback(
    (queryText: string) => {
      const next = [queryText, ...recentSearches.filter((item) => item !== queryText)].slice(0, 9);
      persistRecentSearches(next);
    },
    [persistRecentSearches, recentSearches],
  );

  const removeFromRecentSearches = useCallback(
    (queryText: string) => {
      const next = recentSearches.filter((item) => item !== queryText);
      persistRecentSearches(next);
    },
    [persistRecentSearches, recentSearches],
  );

  const handleClearSearch = useCallback(() => {
    reset();
    setError(null);
    toast.success("Search cleared");
  }, [reset]);

  const openLightbox = useCallback((src: string, alt?: string) => {
    setLightboxSrc(src);
    setLightboxAlt(alt);
    setLightboxOpen(true);
  }, []);

  const runSearch = useCallback(
    async (queryText: string) => {
      if (!isReady) {
        toast.error("Start the backend first", {
          description: "Initialize the Snappy services before running a search.",
        });
        return;
      }

      setLoading(true);
      setError(null);
      setHasSearched(true);
      addToRecentSearches(queryText);

      try {
        const started = performance.now();
        const raw = await RetrievalService.searchSearchGet(queryText, k);
        const data = parseSearchResults(raw);
        const finished = performance.now();
        setResults(data, finished - started);
        toast.success(
          data.length === 1 ? "Found 1 result" : `Found ${data.length} results`,
          {
            description: finished && started ? `Loaded in ${(finished - started).toFixed(0)} ms` : undefined,
          },
        );
      } catch (err) {
        let message = "Search failed";
        if (err instanceof ApiError) {
          message = `${err.status}: ${err.message}`;
        } else if (err instanceof Error) {
          message = err.message;
        }
        setError(message);
        toast.error("Search failed", { description: message });
      } finally {
        setLoading(false);
      }
    },
    [addToRecentSearches, isReady, k, setHasSearched, setResults],
  );

  const handleSubmit = useCallback(
    (event: React.FormEvent) => {
      event.preventDefault();
      const value = query.trim();
      if (!value) return;
      void runSearch(value);
    },
    [query, runSearch],
  );

  return (
    <div className="flex min-h-screen flex-col">
      {/* Header Section */}
      <div className="border-b bg-gradient-to-br from-purple-500/5 to-background px-6 py-12 sm:px-8 lg:px-12">
        <div className="mx-auto max-w-7xl">
          <motion.div {...fadeIn} className="space-y-4">
            <div className="flex items-center gap-3">
              <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-purple-500/10">
                <SearchIcon className="h-6 w-6 text-purple-600 dark:text-purple-400" />
              </div>
              <div>
                <h1 className="text-3xl font-bold tracking-tight text-foreground sm:text-4xl">
                  Visual Search
                </h1>
                <p className="text-sm text-muted-foreground sm:text-base">
                  AI-powered document search with visual understanding
                </p>
              </div>
            </div>
          </motion.div>
        </div>
      </div>

      <div className="mx-auto w-full max-w-7xl flex-1 px-6 py-8 sm:px-8 lg:px-12">
        <div className="grid gap-6 lg:grid-cols-[1fr_300px]">
          {/* Main Content */}
          <div className="space-y-6">
            <SystemStatusWarning isReady={isReady} isLoading={statusLoading} className="rounded-2xl" />

            {/* Search Card */}
            <Card className="border-2">
              <CardHeader className="border-b bg-muted/30">
                <CardTitle className="text-lg font-semibold">Search Query</CardTitle>
                <CardDescription>Describe what you're looking for using natural language</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6 pt-6">
                <SearchBar
                  q={query}
                  setQ={setQuery}
                  loading={loading}
                  onSubmit={handleSubmit}
                  k={k}
                  setK={setK}
                  topK={topK}
                  setTopK={setTopK}
                  onClear={handleClearSearch}
                  hasResults={hasResults}
                  inputRef={inputRef}
                  recentSearches={recentSearches}
                  onSelectRecent={setQuery}
                  onRemoveRecent={removeFromRecentSearches}
                />

                {!hasSearched && !loading && (
                  <div className="space-y-3">
                    <span className="text-sm font-medium text-muted-foreground">Quick examples:</span>
                    <div className="flex flex-wrap gap-2">
                      {EXAMPLE_QUERIES.map((example) => (
                        <Button
                          key={example}
                          type="button"
                          variant="outline"
                          size="sm"
                          onClick={() => setQuery(example)}
                          className="rounded-full text-xs"
                        >
                          {example}
                        </Button>
                      ))}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>

            <AnimatePresence>
              {error && (
                <motion.div {...fadeIn} key="error">
                  <Alert variant="destructive">
                    <AlertCircle className="h-4 w-4" />
                    <AlertDescription>{error}</AlertDescription>
                  </Alert>
                </motion.div>
              )}
            </AnimatePresence>

            {/* Results Section */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h2 className="text-xl font-semibold text-foreground">
                  {hasResults
                    ? `${results.length} Result${results.length === 1 ? "" : "s"}`
                    : "Results"}
                </h2>
                {typeof searchDurationMs === "number" && hasResults && (
                  <Badge variant="secondary" className="text-xs">
                    {searchDurationMs.toFixed(0)}ms
                  </Badge>
                )}
              </div>

              <AnimatePresence mode="wait">
                {loading ? (
                  <motion.div
                    key="loading"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3"
                  >
                    {Array.from({ length: 6 }).map((_, index) => (
                      <div key={index} className="space-y-3 rounded-xl border border-dashed border-muted p-4">
                        <div className="aspect-video rounded-lg bg-muted/40 animate-pulse" />
                        <div className="space-y-2">
                          <div className="h-4 w-3/4 rounded bg-muted/60 animate-pulse" />
                          <div className="h-3 w-1/2 rounded bg-muted/50 animate-pulse" />
                        </div>
                      </div>
                    ))}
                  </motion.div>
                ) : hasResults ? (
                  <motion.div
                    key="results"
                    initial="initial"
                    animate="animate"
                    variants={{
                      initial: { opacity: 0, y: 8 },
                      animate: { opacity: 1, y: 0, transition: { staggerChildren: 0.04 } },
                    }}
                    className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3"
                  >
                    {results.map((item, index) => (
                      <motion.div
                        key={index}
                        variants={{ initial: { opacity: 0, y: 8 }, animate: { opacity: 1, y: 0 } }}
                      >
                        <ResultCard item={item} index={index} onPreview={openLightbox} />
                      </motion.div>
                    ))}
                  </motion.div>
                ) : (
                  hasSearched && (
                    <motion.div
                      key="empty"
                      initial={{ opacity: 0, y: 8 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: 8 }}
                      className="flex flex-col items-center gap-4 rounded-xl border border-dashed border-muted bg-muted/20 p-12 text-center"
                    >
                      <div className="flex size-16 items-center justify-center rounded-full bg-muted text-muted-foreground">
                        <ImageIcon className="h-8 w-8" />
                      </div>
                      <div className="space-y-2">
                        <h3 className="text-lg font-semibold text-foreground">No matches found</h3>
                        <p className="text-sm text-muted-foreground max-w-md">
                          Try different phrasing, broaden your query, or upload more documents to expand the search database.
                        </p>
                      </div>
                    </motion.div>
                  )
                )}
              </AnimatePresence>
            </div>
          </div>

          {/* Sidebar */}
          <div className="space-y-6 lg:sticky lg:top-6 lg:h-fit">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Search Tips</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 text-sm text-muted-foreground">
                <div className="space-y-2">
                  <p className="font-medium text-foreground">Be specific</p>
                  <p>Describe visual elements like charts, tables, or diagrams.</p>
                </div>
                <div className="space-y-2">
                  <p className="font-medium text-foreground">Use context</p>
                  <p>Include colors, layouts, or text snippets you remember.</p>
                </div>
                <div className="space-y-2">
                  <p className="font-medium text-foreground">Try variations</p>
                  <p>Rephrase your query if the first attempt doesn't match.</p>
                </div>
              </CardContent>
            </Card>

            {recentSearches.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Recent Searches</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  {recentSearches.slice(0, 5).map((search) => (
                    <button
                      key={search}
                      onClick={() => setQuery(search)}
                      className="w-full truncate rounded-lg border px-3 py-2 text-left text-sm transition-colors hover:bg-muted"
                    >
                      {search}
                    </button>
                  ))}
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </div>

      <ImageLightbox
        open={lightboxOpen}
        src={lightboxSrc}
        alt={lightboxAlt}
        onOpenChange={setLightboxOpen}
      />
    </div>
  );
}

function ResultCard({
  item,
  index,
  onPreview,
}: {
  item: SearchItem;
  index: number;
  onPreview: (src: string, alt?: string) => void;
}) {
  const imageSrc: string | null =
    (item.payload?.image_url as string | undefined) ?? (item.payload?.image_base64 ? `data:image/png;base64,${item.payload.image_base64}` : null);
  const isInline = Boolean(item.payload?.image_base64);

  return (
    <Card className="overflow-hidden">
      <div className="relative aspect-video bg-muted">
        {imageSrc ? (
          <button
            type="button"
            onClick={() => onPreview(imageSrc, item.label ?? `Result ${index + 1}`)}
            className="group relative flex h-full w-full items-center justify-center overflow-hidden"
          >
            <Image
              src={imageSrc}
              alt={item.label ?? `Result ${index + 1}`}
              fill
              className="object-cover transition-transform duration-300 group-hover:scale-105"
              sizes="(max-width: 640px) 100vw, (max-width: 1280px) 50vw, 33vw"
              unoptimized={isInline}
            />
            <span className="absolute bottom-3 right-3 inline-flex items-center gap-1 rounded-full bg-background/90 px-2 py-1 text-xs font-medium text-foreground shadow-sm transition-opacity group-hover:opacity-100">
              Preview
            </span>
          </button>
        ) : (
          <div className="flex h-full w-full items-center justify-center text-muted-foreground">
            <ImageIcon className="h-8 w-8" />
          </div>
        )}
      </div>
      <CardContent className="space-y-3 py-4">
        <div className="space-y-1">
          <h3 className="line-clamp-2 text-base font-semibold text-foreground">
            {item.label ?? `Result ${index + 1}`}
          </h3>
          {item.payload?.filename && (
            <p className="text-sm text-muted-foreground">
              {item.payload.filename}
              {typeof item.payload?.pdf_page_index === "number" && ` - Page ${item.payload.pdf_page_index + 1}`}
            </p>
          )}
        </div>
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <Badge variant="secondary">#{index + 1}</Badge>
          {typeof item.score === "number" && (
            <Badge variant="outline">{Math.round(item.score * 100)}%</Badge>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
