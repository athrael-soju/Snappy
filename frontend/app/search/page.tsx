"use client";

import { useState, useEffect, useCallback, useRef, useMemo } from "react";
import type { SearchItem } from "@/lib/api/generated";
import { RetrievalService, ApiError, MaintenanceService } from "@/lib/api/generated";
import "@/lib/api/client";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Search, AlertCircle, ImageIcon, Eye, ExternalLink } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { defaultPageMotion, fadeInItemMotion, fadeInPresence, hoverLift, sectionVariants, staggeredListMotion } from "@/lib/motion-presets";
import { toast } from "@/components/ui/sonner";
import Image from "next/image";
import ImageLightbox from "@/components/lightbox";
import SearchBar from "@/components/search/SearchBar";
import { useSearchStore, useSystemStatus } from "@/stores/app-store";
import { PageHeader } from "@/components/page-header";
import { SystemStatusWarning } from "@/components/upload";


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
      const status = await MaintenanceService.getStatusStatusGet();
      setStatus({ ...status, lastChecked: Date.now() });
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
      const data = await RetrievalService.searchSearchGet(query, k);
      const end = performance.now();
      setResults(data, end - start);

      toast.success(`Found ${data.length} ${data.length === 1 ? "result" : "results"}`, {
        description: filterSummary ? `Filters active: ${filterSummary}` : undefined,
      });
    } catch (err: unknown) {
      let errorMsg = "Search failed";
      if (err instanceof ApiError) {
        errorMsg = `${err.status}: ${err.message}`;
      } else if (err instanceof Error) {
        errorMsg = err.message;
      }
      setError(errorMsg);
      toast.error("Search Failed", { description: errorMsg });
    } finally {
      setLoading(false);
    }
  }

  return (
    <motion.div {...defaultPageMotion} className="page-shell flex min-h-0 flex-1 flex-col gap-8">
      <motion.section variants={sectionVariants} className="pt-8 sm:pt-12">
        <PageHeader
          title="Visual Search"
          description="Find documents and images using natural language powered by AI vision."
          icon={Search}
        />
      </motion.section>

      <motion.section variants={sectionVariants} className="flex min-h-0 flex-1 flex-col gap-6 pb-8 sm:pb-12">
        <SystemStatusWarning isReady={isReady} />

        <div className="sticky top-[5.25rem] z-30">
          <Card className="card-surface shadow-none">
            <CardContent className="space-y-4 py-5">
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
            </CardContent>
          </Card>
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

        <ScrollArea className="custom-scrollbar h-[calc(100vh-30rem)]">
          <div className="space-y-6 p-4 pb-10">
            {!hasSearched && !loading && !error ? (
              <Card className="card-surface border border-dashed border-muted/60 text-center">
                <CardContent className="flex flex-col items-center gap-6 py-16">
                  <div className="flex size-20 items-center justify-center rounded-full bg-[color:var(--surface-2)] text-primary">
                    <Search className="h-9 w-9" />
                  </div>
                  <div className="space-y-3 max-w-2xl">
                    <h3 className="text-2xl font-semibold text-foreground">Search across documents, slides, and imagery</h3>
                    <p className="text-base text-muted-foreground">
                      Describe what you are looking for, combine visual details with text cues, and refine faster with filters and keyboard shortcuts.
                    </p>
                  </div>
                  <div className="grid gap-2 sm:grid-cols-2">
                    {exampleQueries.map((example) => (
                      <Button
                        key={example}
                        type="button"
                        variant="outline"
                        onClick={() => setQ(example)}
                        className="justify-start rounded-xl border-muted px-4 py-3 text-left text-sm text-muted-foreground hover:border-primary/40 hover:bg-primary/10 hover:text-foreground"
                      >
                        {example}
                      </Button>
                    ))}
                  </div>
                </CardContent>
              </Card>
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
                        <Card className="group flex h-full flex-col overflow-hidden border border-muted bg-[color:var(--surface-1)] shadow-[var(--shadow-1)] transition will-change-transform hover:-translate-y-1 hover:shadow-[var(--shadow-2)]">
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
                                className="object-cover transition duration-500 group-hover:scale-105"
                              />
                              <div className="absolute inset-0 bg-gradient-to-t from-black/45 via-transparent to-transparent opacity-0 transition-opacity duration-300 group-hover:opacity-100" />
                              <span className="absolute right-3 top-3 inline-flex items-center gap-1 rounded-full border border-transparent bg-white/90 px-3 py-1 text-xs font-semibold text-slate-700 shadow-sm">
                                <Eye className="h-3.5 w-3.5" /> View
                              </span>
                            </button>
                          ) : (
                            <div className="flex aspect-video items-center justify-center bg-[color:var(--surface-2)]">
                              <ImageIcon className="h-8 w-8 text-muted-foreground" />
                            </div>
                          )}

                          <CardContent className="flex flex-1 flex-col gap-4 p-4">
                            <div className="space-y-1">
                              <h3 className="line-clamp-2 text-base font-semibold text-foreground group-hover:text-primary">
                                {item.label ?? `Result ${idx + 1}`}
                              </h3>
                              {item.payload?.filename && (
                                <p className="line-clamp-1 text-xs text-muted-foreground">
                                  {item.payload.filename}
                                  {item.payload?.pdf_page_index !== undefined && ` • Page ${item.payload.pdf_page_index + 1}`}
                                </p>
                              )}
                            </div>

                            <div className="mt-auto flex items-center justify-between border-t border-divider pt-3 text-xs text-muted-foreground">
                              <div className="flex items-center gap-2">
                                <Badge variant="outline" className="border-muted bg-[color:var(--surface-0)]/70 text-xs font-medium">
                                  #{idx + 1}
                                </Badge>
                                {typeof item.score === "number" && (
                                  <Badge variant="outline" className="border-muted bg-[color:var(--surface-0)]/70 text-xs font-medium">
                                    Score {Math.round(item.score * 100)}
                                  </Badge>
                                )}
                              </div>
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
                    <Card className="card-surface">
                      <CardContent className="flex flex-col items-center gap-6 py-14 text-center">
                        <div className="flex size-20 items-center justify-center rounded-full bg-[color:var(--surface-2)]">
                          <ImageIcon className="h-10 w-10 text-muted-foreground" />
                        </div>
                        <div className="space-y-3 max-w-xl">
                          <h3 className="text-xl font-semibold text-foreground">No matches found</h3>
                          <p className="text-base text-muted-foreground">
                            We could not find results for <span className="font-medium text-foreground">{q}</span>. Adjust your search terms, broaden filters, or upload additional documents to improve coverage.
                          </p>
                        </div>
                        <div className="grid gap-2 text-sm text-muted-foreground sm:grid-cols-2">
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
                      </CardContent>
                    </Card>
                  </motion.div>
                )}
              </AnimatePresence>
            )}
          </div>
        </ScrollArea>
      </motion.section>

      <ImageLightbox open={lightboxOpen} src={lightboxSrc} alt={lightboxAlt} onOpenChange={setLightboxOpen} />
    </motion.div>
  );
}
