"use client";

import { useState, useEffect, useCallback, useRef, useMemo } from "react";
import { zodClient } from "@/lib/api/client";
import type { SearchItem } from "@/lib/api/zod-types";
import { getErrorMessage } from "@/lib/api/errors";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Search, AlertCircle, ImageIcon, Eye, ExternalLink } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { defaultPageMotion, fadeInItemMotion, fadeInPresence, hoverLift, sectionVariants, staggeredListMotion } from "@/lib/motion-presets";
import { toast } from "@/components/ui/sonner";
import { GlassPanel } from "@/components/ui/glass-panel";
import Image from "next/image";
import ImageLightbox from "@/components/lightbox";
import SearchBar from "@/components/search/SearchBar";
import { useSearchStore, useSystemStatus } from "@/stores/app-store";
import { PageHeader } from "@/components/page-header";
import { SystemStatusWarning } from "@/components/upload";
import type { SystemStatus } from "@/components/maintenance/types";


const exampleQueries = [
  "Show pitch decks with charts on revenue targets",
  "Contracts mentioning service level agreements",
  "Images that include architectural diagrams",
  "Team updates from the past quarter",
];

const fileTypeOptions = ["All types", "Documents", "Images"];
const dateRangeOptions = ["Any time", "Past week", "Past month", "Past year"];
const sourceOptions = ["All sources", "Uploads", "External"];

type FilterState = {
  fileType: number;
  dateRange: number;
  source: number;
  hasImages: boolean;
};

const defaultFilters: FilterState = {
  fileType: 0,
  dateRange: 0,
  source: 0,
  hasImages: false,
};

export default function SearchPage() {
  const {
    query: q,
    results,
    hasSearched,
    searchDurationMs,
    k,
    topK,
    setQuery: setQ,
    setResults,
    setHasSearched,
    setK,
    setTopK,
    reset,
  } = useSearchStore();
  const { setStatus, isReady } = useSystemStatus();

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [statusLoading, setStatusLoading] = useState(false);
  const [lightboxOpen, setLightboxOpen] = useState(false);
  const [lightboxSrc, setLightboxSrc] = useState("");
  const [lightboxAlt, setLightboxAlt] = useState<string | undefined>(undefined);
  const [recentSearches, setRecentSearches] = useState<string[]>([]);
  const [filters, setFilters] = useState<FilterState>(defaultFilters);

  const hasFetchedRef = useRef(false);
  const searchInputRef = useRef<HTMLInputElement>(null!);

  const hasResults = hasSearched && results.length > 0;

  const fetchSystemStatus = useCallback(async () => {
    setStatusLoading(true);
    try {
      const status = await zodClient.get("/status");
      setStatus({ ...(status as SystemStatus), lastChecked: Date.now() });
      hasFetchedRef.current = true;
    } catch (err) {
      console.error("Failed to fetch system status:", err);
    } finally {
      setStatusLoading(false);
    }
  }, [setStatus]);

  useEffect(() => {
    if (!hasFetchedRef.current) {
      fetchSystemStatus();
    }

    window.addEventListener("systemStatusChanged", fetchSystemStatus);
    return () => {
      window.removeEventListener("systemStatusChanged", fetchSystemStatus);
    };
  }, [fetchSystemStatus]);

  useEffect(() => {
    const saved = localStorage.getItem("colpali-recent-searches");
    if (saved) {
      try {
        setRecentSearches(JSON.parse(saved));
      } catch {
        // ignore parse errors
      }
    }
  }, []);

  const addToRecentSearches = useCallback((query: string) => {
    const updated = [query, ...recentSearches.filter((s) => s !== query)].slice(0, 5);
    setRecentSearches(updated);
    localStorage.setItem("colpali-recent-searches", JSON.stringify(updated));
  }, [recentSearches]);

  const removeFromRecentSearches = useCallback((query: string) => {
    const updated = recentSearches.filter((s) => s !== query);
    setRecentSearches(updated);
    localStorage.setItem("colpali-recent-searches", JSON.stringify(updated));
  }, [recentSearches]);

  const handleClearSearch = useCallback(() => {
    reset();
    setError(null);
    toast.success("Search results cleared");
  }, [reset]);

  const cycleFilter = useCallback((key: keyof FilterState) => {
    setFilters((prev) => {
      if (key === "hasImages") {
        return { ...prev, hasImages: !prev.hasImages };
      }

      const max = key === "fileType" ? fileTypeOptions.length : key === "dateRange" ? dateRangeOptions.length : sourceOptions.length;
      const nextIndex = (prev[key] as number + 1) % max;
      return { ...prev, [key]: nextIndex } as FilterState;
    });
  }, []);

  const filterSummary = useMemo(() => {
    const summary: string[] = [];
    if (filters.fileType !== 0) summary.push(fileTypeOptions[filters.fileType]);
    if (filters.dateRange !== 0) summary.push(dateRangeOptions[filters.dateRange]);
    if (filters.source !== 0) summary.push(sourceOptions[filters.source]);
    if (filters.hasImages) summary.push("Has images");
    return summary.join(" � ");
  }, [filters]);

  useEffect(() => {
    const handler = (event: KeyboardEvent) => {
      if (event.key === "/" && !event.metaKey && !event.ctrlKey && !event.altKey) {
        event.preventDefault();
        searchInputRef.current?.focus();
      }

      if (event.key === "Escape") {
        if (loading) return;
        if (document.activeElement === searchInputRef.current && q) {
          setQ("");
          return;
        }
        if (hasResults) {
          handleClearSearch();
        }
      }
    };

    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [handleClearSearch, hasResults, loading, q, setQ]);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    const query = q.trim();
    if (!query) return;

    if (!isReady) {
      toast.error("System Not Ready", {
        description: "Initialize collection and bucket before searching",
      });
      return;
    }

    setLoading(true);
    setError(null);
    setHasSearched(true);
    addToRecentSearches(query);

    try {
      const start = performance.now();
      const data = await zodClient.get("/search", {
        queries: {
          q: query,
          k,
        },
      });
      const end = performance.now();
      setResults(data as SearchItem[], end - start);

      toast.success(`Found ${data.length} ${data.length === 1 ? "result" : "results"}`, {
        description: filterSummary ? `Filters active: ${filterSummary}` : undefined,
      });
    } catch (err: unknown) {
      const errorMsg = getErrorMessage(err, "Search failed");
      setError(errorMsg);
      toast.error("Search Failed", { description: errorMsg });
    } finally {
      setLoading(false);
    }
  }

  return (
    <motion.div {...defaultPageMotion} className="page-shell flex min-h-0 flex-1 flex-col gap-6">
      <motion.section variants={sectionVariants} className="flex flex-col items-center text-center gap-6 pt-6 sm:pt-8">
        <PageHeader
          title="Visual Search"
          icon={Search}
          tooltip="Find documents and images using natural language powered by AI vision"
        />
      </motion.section>

      <motion.section variants={sectionVariants} className="flex-1 min-h-0 flex flex-col gap-6 pb-6 sm:pb-8">
        <div className="mx-auto flex h-full w-full max-w-6xl flex-1 flex-col gap-6">
          <SystemStatusWarning isReady={isReady} />

          <div className="sticky top-[5.25rem] z-30">
            <GlassPanel className="p-5 overflow-visible">
              <SearchBar
                q={q}
                setQ={setQ}
                loading={loading}
                onSubmit={onSubmit}
                k={k}
                setK={setK}
                topK={topK}
                setTopK={setTopK}
                hasResults={hasResults}
                onClear={handleClearSearch}
                inputRef={searchInputRef}
                recentSearches={recentSearches}
                onSelectRecent={setQ}
                onRemoveRecent={removeFromRecentSearches}
              />
            </GlassPanel>
          </div>

          <AnimatePresence>
            {error && (
              <motion.div variants={fadeInPresence} initial="hidden" animate="visible" exit="exit">
                <Alert variant="destructive" className="border-strong bg-destructive/10 text-foreground">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              </motion.div>
            )}
          </AnimatePresence>

          <ScrollArea className="h-[calc(100vh-30rem)]">
            <div className="px-1 py-2 pr-4">
              {!hasSearched && !loading && !error ? (
                <GlassPanel className="p-20 text-center">
                  <div className="flex size-20 items-center justify-center rounded-2xl bg-gradient-to-br from-primary/10 to-primary/5 text-primary">
                    <Search className="h-9 w-9" />
                  </div>
                  <div className="space-y-3 max-w-2xl">
                    <h3 className="text-2xl font-semibold text-foreground">Search across documents, slides, and imagery</h3>
                    <p className="text-base leading-relaxed text-muted-foreground">
                      Find documents using natural language. Try one of the examples below to get started.
                    </p>
                  </div>
                  <div className="grid gap-3 sm:grid-cols-2">
                    {exampleQueries.map((example) => (
                      <Button
                        key={example}
                        type="button"
                        variant="outline"
                        onClick={() => setQ(example)}
                        className="justify-start rounded-xl px-4 py-3 text-left text-base hover:border-primary/40 hover:bg-primary/10"
                      >
                        {example}
                      </Button>
                    ))}
                  </div>
                </GlassPanel>
              ) : (
                <AnimatePresence mode="wait">
                  {loading ? (
                    <motion.div
                      key="skeleton"
                      {...staggeredListMotion}
                      className="grid gap-6 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4"
                    >
                      {Array.from({ length: 8 }).map((_, idx) => (
                        <motion.div key={idx} {...fadeInItemMotion} className="card-surface h-full animate-pulse space-y-3 p-4">
                          <div className="aspect-video rounded-xl bg-[color:var(--surface-2)]" />
                          <div className="space-y-2">
                            <div className="h-4 w-3/4 rounded bg-[color:var(--surface-2)]" />
                            <div className="h-3 w-2/3 rounded bg-[color:var(--surface-2)]" />
                          </div>
                          <div className="h-3 w-1/3 rounded bg-[color:var(--surface-2)]" />
                        </motion.div>
                      ))}
                    </motion.div>
                  ) : hasResults ? (
                    <motion.div
                      key="results"
                      {...staggeredListMotion}
                      className="grid gap-6 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4"
                    >
                      {results.map((item, idx) => (
                        <motion.div key={idx} {...fadeInItemMotion} {...hoverLift}>
                          <Card className="card-surface group flex h-full flex-col overflow-hidden cursor-pointer hover:shadow-xl transition-all border-border/50">
                            {item.image_url ? (
                              <button
                                type="button"
                                className="relative aspect-video overflow-hidden text-left"
                                onClick={() => {
                                  setLightboxSrc(item.image_url!);
                                  setLightboxAlt(item.label ?? `Result ${idx + 1}`);
                                  setLightboxOpen(true);
                                }}
                              >
                                <Image
                                  src={item.image_url}
                                  alt={item.label ?? `Result ${idx + 1}`}
                                  fill
                                  sizes="(max-width: 640px) 100vw, (max-width: 1280px) 50vw, 25vw"
                                  className="object-cover transition duration-500 group-hover:scale-110"
                                />
                                <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent opacity-0 transition-opacity duration-300 group-hover:opacity-100" />
                                <span className="absolute right-3 top-3 inline-flex items-center gap-1 rounded-full bg-white/95 backdrop-blur-sm px-3 py-1.5 text-xs font-semibold text-slate-700 shadow-lg opacity-0 group-hover:opacity-100 transition-all">
                                  <Eye className="h-3.5 w-3.5" /> View
                                </span>
                              </button>
                            ) : (
                              <div className="flex aspect-video items-center justify-center bg-[color:var(--surface-2)]">
                                <ImageIcon className="h-8 w-8 text-muted-foreground" />
                              </div>
                            )}

                            <CardContent className="flex flex-1 flex-col gap-4 p-4">
                              <div className="space-y-2">
                                <h3 className="line-clamp-2 text-base font-semibold text-foreground group-hover:text-primary transition-colors">
                                  {item.label ?? `Result ${idx + 1}`}
                                </h3>
                                {item.payload?.filename && (
                                  <p className="line-clamp-1 text-sm text-muted-foreground">
                                    {item.payload.filename}
                                    {item.payload?.pdf_page_index !== undefined && ` • Page ${item.payload.pdf_page_index + 1}`}
                                  </p>
                                )}
                              </div>

                              <div className="mt-auto flex items-center gap-2 border-t border-divider pt-3 text-xs">
                                <Badge variant="secondary" className="text-xs font-medium rounded-full">
                                  #{idx + 1}
                                </Badge>
                                {typeof item.score === "number" && (
                                  <Badge variant="outline" className="text-xs font-medium rounded-full border-primary/30 text-primary">
                                    {Math.round(item.score * 100)}%
                                  </Badge>
                                )}
                              </div>
                            </CardContent>
                          </Card>
                        </motion.div>
                      ))}
                    </motion.div>
                  ) : (
                    <motion.div
                      key="empty"
                      variants={fadeInPresence}
                      initial="hidden"
                      animate="visible"
                      exit="exit"
                    >
                      <GlassPanel className="p-14">
                        <div className="flex flex-col items-center gap-6 text-center">
                          <div className="flex size-20 items-center justify-center rounded-2xl bg-gradient-to-br from-muted/30 to-muted/10">
                            <ImageIcon className="h-10 w-10 text-muted-foreground" />
                          </div>
                          <div className="space-y-3 max-w-xl">
                            <h3 className="text-xl font-semibold text-foreground">No matches found</h3>
                            <p className="text-base leading-relaxed text-muted-foreground">
                              We could not find results for <span className="font-medium text-foreground">{q}</span>. Adjust your search terms, broaden filters, or upload additional documents to improve coverage.
                            </p>
                          </div>
                          <div className="grid gap-3 text-base text-muted-foreground sm:grid-cols-2">
                            <div className="flex items-start gap-2">
                              <span className="mt-1 size-1.5 rounded-full bg-foreground/70" />
                              Try pairing a document title with a visual clue.
                            </div>
                            <div className="flex items-start gap-2">
                              <span className="mt-1 size-1.5 rounded-full bg-foreground/70" />
                              Check spelling or use broader keywords.
                            </div>
                            <div className="flex items-start gap-2">
                              <span className="mt-1 size-1.5 rounded-full bg-foreground/70" />
                              Narrow filters or reset them to defaults.
                            </div>
                            <div className="flex items-start gap-2">
                              <span className="mt-1 size-1.5 rounded-full bg-foreground/70" />
                              Upload more visuals for richer retrieval.
                            </div>
                          </div>
                        </div>
                      </GlassPanel>
                    </motion.div>
                  )}
                </AnimatePresence>
              )}

            </div>
          </ScrollArea>
        </div>
      </motion.section>

      <ImageLightbox open={lightboxOpen} src={lightboxSrc} alt={lightboxAlt} onOpenChange={setLightboxOpen} />
    </motion.div>
  );
}
