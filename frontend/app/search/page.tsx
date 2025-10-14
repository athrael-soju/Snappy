"use client";

import { useState, useEffect, useCallback, useRef, useMemo } from "react";
import { parseSearchResults, type SearchItem } from "@/lib/api/runtime";
import { RetrievalService, ApiError, MaintenanceService } from "@/lib/api/generated";
import "@/lib/api/client";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
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

    try {
      const start = performance.now();
      const rawData = await RetrievalService.searchSearchGet(query, k);
      const data = parseSearchResults(rawData);
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
    <motion.div {...defaultPageMotion} className="page-shell flex flex-col gap-4 h-screen overflow-hidden py-4">
      <motion.section variants={sectionVariants} className="flex-shrink-0">
        <PageHeader
          title="Visual Search"
          icon={Search}
          tooltip="Find documents and images using natural language powered by AI vision"
        />
      </motion.section>

      <motion.section variants={sectionVariants} className="flex-1 flex flex-col gap-4 min-h-0">
        <div className="mx-auto w-full max-w-6xl flex flex-col gap-4 h-full">
          <SystemStatusWarning isReady={isReady} />

          <div className="flex-shrink-0">
            <GlassPanel className="p-4">
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
              />
            </GlassPanel>
          </div>

          <AnimatePresence>
            {error && (
              <motion.div variants={fadeInPresence} initial="hidden" animate="visible" exit="exit" className="flex-shrink-0">
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              </motion.div>
            )}
          </AnimatePresence>

          <div className="flex-1 overflow-y-auto min-h-0">
            {!hasSearched && !loading && !error ? (
                <GlassPanel className="p-8 sm:p-12">
                  <div className="flex flex-col items-center gap-8 text-center">
                    <div className="space-y-4 max-w-xl">
                      <div className="flex size-14 items-center justify-center rounded-xl icon-bg text-primary mx-auto">
                        <Search className="h-6 w-6" />
                      </div>
                      
                      <div className="space-y-2">
                        <h3 className="text-lg font-semibold">
                          Search across documents, slides, and imagery
                        </h3>
                        <p className="text-sm text-muted-foreground">
                          Find documents using natural language. Try one of the examples below to get started.
                        </p>
                      </div>
                    </div>
                    
                    <div className="w-full max-w-2xl space-y-3">
                      <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Example queries</p>
                      <div className="grid gap-2 sm:grid-cols-2">
                        {exampleQueries.map((example) => (
                          <Button
                            key={example}
                            type="button"
                            variant="outline"
                            onClick={() => setQ(example)}
                            className="justify-start h-auto min-h-[2.5rem] text-left hover-interactive"
                          >
                            <span className="line-clamp-2 text-sm">{example}</span>
                          </Button>
                        ))}
                      </div>
                    </div>
                  </div>
                </GlassPanel>
              ) : (
                <AnimatePresence mode="wait">
                  {loading ? (
                    <motion.div
                      key="skeleton"
                      {...staggeredListMotion}
                      className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4"
                    >
                      {Array.from({ length: 8 }).map((_, idx) => (
                        <Card key={idx} className="h-full animate-pulse">
                          <div className="aspect-video bg-muted" />
                          <CardContent className="space-y-3 p-4">
                            <div className="space-y-2">
                              <div className="h-4 w-3/4 rounded bg-muted" />
                              <div className="h-3 w-2/3 rounded bg-muted" />
                            </div>
                            <div className="h-3 w-1/3 rounded bg-muted" />
                          </CardContent>
                        </Card>
                      ))}
                    </motion.div>
                  ) : hasResults ? (
                    <motion.div
                      key="results"
                      {...staggeredListMotion}
                      className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4"
                    >
                      {results.map((item, idx) => {
                        const imageSrc = item.image_url ?? "";
                        const hasImage = imageSrc.length > 0;
                        const isInlineImage = hasImage && imageSrc.startsWith("data:");

                        return (
                          <motion.div key={idx} {...fadeInItemMotion}>
                            <Card className="group flex h-full flex-col overflow-hidden cursor-pointer hover:shadow-lg transition-shadow">
                              {hasImage ? (
                                <button
                                  type="button"
                                  className="relative aspect-video overflow-hidden"
                                  onClick={() => {
                                    setLightboxSrc(imageSrc);
                                    setLightboxAlt(item.label ?? `Result ${idx + 1}`);
                                    setLightboxOpen(true);
                                  }}
                                >
                                  <Image
                                    src={imageSrc}
                                    alt={item.label ?? `Result ${idx + 1}`}
                                    fill
                                    sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 33vw"
                                    className="object-cover"
                                    unoptimized={isInlineImage}
                                  />
                                  <div className="absolute inset-0 bg-black/0 group-hover:bg-black/20 transition-colors" />
                                  <Badge className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                    <Eye className="h-3 w-3 mr-1" /> View
                                  </Badge>
                                </button>
                              ) : (
                                <div className="flex aspect-video items-center justify-center bg-muted">
                                  <ImageIcon className="h-8 w-8 text-muted-foreground" />
                                </div>
                              )}

                              <CardContent className="flex flex-1 flex-col gap-3 p-4">
                                <div className="space-y-1">
                                  <h3 className="line-clamp-2 text-sm font-semibold">
                                    {item.label ?? `Result ${idx + 1}`}
                                  </h3>
                                  {item.payload?.filename && (
                                    <p className="line-clamp-1 text-xs text-muted-foreground">
                                      {item.payload.filename}
                                      {item.payload?.pdf_page_index !== undefined && ` • Page ${item.payload.pdf_page_index + 1}`}
                                    </p>
                                  )}
                                </div>

                                <div className="mt-auto flex items-center gap-2 border-t pt-2">
                                  <Badge variant="secondary" className="text-xs">
                                    #{idx + 1}
                                  </Badge>
                                  {typeof item.score === "number" && (
                                    <Badge variant="outline" className="text-xs">
                                      {Math.round(item.score * 100)}%
                                    </Badge>
                                  )}
                                </div>
                              </CardContent>
                            </Card>
                          </motion.div>
                        );
                      })}
                    </motion.div>
                  ) : (
                    <motion.div
                      key="empty"
                      variants={fadeInPresence}
                      initial="hidden"
                      animate="visible"
                      exit="exit"
                    >
                      <GlassPanel className="p-8 sm:p-12">
                        <div className="flex flex-col items-center gap-6 text-center">
                          <div className="flex size-16 items-center justify-center rounded-xl icon-bg-muted">
                            <ImageIcon className="h-8 w-8 text-muted-foreground" />
                          </div>
                          
                          <div className="space-y-2 max-w-xl">
                            <h3 className="text-lg font-semibold">No matches found</h3>
                            <p className="text-sm text-muted-foreground">
                              We could not find results for <span className="font-medium text-foreground">{q}</span>. Try adjusting your search terms or upload more documents.
                            </p>
                          </div>
                          
                          <div className="grid gap-2 text-sm text-muted-foreground text-left max-w-md w-full">
                            <div className="flex items-start gap-2">
                              <span className="mt-1.5 size-1 rounded-full bg-current flex-shrink-0" />
                              <span>Try pairing a document title with a visual clue.</span>
                            </div>
                            <div className="flex items-start gap-2">
                              <span className="mt-1.5 size-1 rounded-full bg-current flex-shrink-0" />
                              <span>Check spelling or use broader keywords.</span>
                            </div>
                            <div className="flex items-start gap-2">
                              <span className="mt-1.5 size-1 rounded-full bg-current flex-shrink-0" />
                              <span>Upload more visuals for richer retrieval.</span>
                            </div>
                          </div>
                        </div>
                      </GlassPanel>
                    </motion.div>
                  )}
                </AnimatePresence>
              )}

          </div>
        </div>
      </motion.section>

      <ImageLightbox open={lightboxOpen} src={lightboxSrc} alt={lightboxAlt} onOpenChange={setLightboxOpen} />
    </motion.div>
  );
}
