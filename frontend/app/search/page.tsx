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
  transition: { duration: 0.3, ease: "easeOut" },
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

  const inputRef = useRef<HTMLInputElement>(null);
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
    <div className="mx-auto flex w-full max-w-5xl flex-1 flex-col gap-6 px-4 py-8 sm:px-6 lg:px-8">
      <motion.section {...fadeIn}>
        <PageHeader
          title="Visual search"
          description="Ask natural language questions and Snappy returns the pages that match—even when the answer lives inside a chart or screenshot."
          icon={SearchIcon}
        />
      </motion.section>

      <SystemStatusWarning isReady={isReady} isLoading={statusLoading} className="rounded-xl" />

      <Card>
        <CardHeader className="border-b pb-4">
          <CardTitle className="text-lg font-semibold">Search your workspace</CardTitle>
          <CardDescription>Describe the slide, chart, or document you need.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6 pt-4">
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
              <span className="text-sm font-medium text-muted-foreground">Try one:</span>
              <div className="flex flex-wrap gap-2">
                {EXAMPLE_QUERIES.map((example) => (
                  <Button
                    key={example}
                    type="button"
                    variant="outline"
                    onClick={() => setQuery(example)}
                    className="rounded-full"
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

      <Card className="flex-1">
        <CardHeader className="border-b pb-4">
          <CardTitle className="text-lg font-semibold">Results</CardTitle>
          <CardDescription>
            {hasResults
              ? `Showing ${results.length} item${results.length === 1 ? "" : "s"}${
                  typeof searchDurationMs === "number" ? ` · ${searchDurationMs.toFixed(0)} ms` : ""
                }`
              : "Search to see matching pages."}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6 pt-4">
          <AnimatePresence mode="wait">
            {loading ? (
              <motion.div
                key="loading"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3"
              >
                {Array.from({ length: 6 }).map((_, index) => (
                  <div key={index} className="space-y-3 rounded-xl border border-dashed border-muted p-4">
                    <div className="aspect-video rounded-lg bg-muted/40" />
                    <div className="space-y-2">
                      <div className="h-4 w-3/4 rounded bg-muted/60" />
                      <div className="h-3 w-1/2 rounded bg-muted/50" />
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
                className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3"
              >
                {results.map((item, index) => (
                  <motion.div
                    key={item.id ?? index}
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
                  className="flex flex-col items-center gap-4 rounded-xl border border-dashed border-muted p-10 text-center"
                >
                  <div className="flex size-16 items-center justify-center rounded-full bg-muted/60 text-muted-foreground">
                    <ImageIcon className="h-8 w-8" />
                  </div>
                  <div className="space-y-2">
                    <h3 className="text-lg font-semibold text-foreground">No matches yet</h3>
                    <p className="text-sm text-muted-foreground">
                      Try different phrasing, broaden the request, or ingest more documents so Snappy has context to work with.
                    </p>
                  </div>
                </motion.div>
              )
            )}
          </AnimatePresence>
        </CardContent>
      </Card>

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
  const imageSrc =
    item.payload?.image_url ?? (item.payload?.image_base64 ? `data:image/png;base64,${item.payload.image_base64}` : null);
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
              {typeof item.payload?.pdf_page_index === "number" && ` · Page ${item.payload.pdf_page_index + 1}`}
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
