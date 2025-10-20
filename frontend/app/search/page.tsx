"use client";

import Link from "next/link";
import { ChangeEvent, FormEvent, useMemo, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import "@/lib/api/client";
import Image from "next/image";
import {
  Search,
  Loader2,
  X,
  AlertCircle,
  Sparkles,
  ArrowRight,
  FileText,
  Clock,
  Compass,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { AppButton } from "@/components/app-button";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { RetrievalService } from "@/lib/api/generated";
import { parseSearchResults } from "@/lib/api/runtime";
import { useSearchStore } from "@/lib/hooks/use-search-store";
import { useSystemStatus } from "@/stores/app-store";
import ImageLightbox from "@/components/lightbox";
import { InfoTooltip } from "@/components/info-tooltip";
import { RoutePageShell } from "@/components/route-page-shell";
import { HeroMetaGroup, HeroMetaPill } from "@/components/hero-meta";

const suggestedQueries = [
  "Show recent upload summaries",
  "Find diagrams about the architecture",
  "Which contracts mention service levels?",
];

type SearchHelperCard = {
  id: string;
  title: string;
  description: string;
  icon: LucideIcon;
  gradient: string;
  href?: string;
  actionLabel?: string;
};

const SEARCH_HELPER_CARDS: SearchHelperCard[] = [
  {
    id: "start",
    title: "Ask Morty anything",
    description: "Morty loves questions about people, diagrams, or document details. He ranks the most relevant visual matches instantly.",
    icon: Sparkles,
    gradient: "from-chart-1 to-chart-2",
  },
  {
    id: "uploads",
    title: "Check what Morty indexed",
    description: "Recently uploaded? Ask Morty to search by filename or topic to verify your latest PDFs are ready.",
    icon: FileText,
    gradient: "from-chart-3 to-chart-4",
    href: "/upload",
    actionLabel: "Go to Upload",
  },
  {
    id: "status",
    title: "Keep Morty healthy",
    description: "Make sure Qdrant and MinIO are ready before big searches so Morty can work at full speed.",
    icon: Compass,
    gradient: "from-chart-2 to-primary",
    href: "/maintenance",
    actionLabel: "Open Maintenance",
  },
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

  const truncatedResults = useMemo(() => results.slice(0, k), [results, k]);

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

  const heroActions = (
    <>
      <AppButton
        asChild
        variant="primary"
        size="xs"
        className="rounded-[var(--radius-button)] bg-white px-5 text-vultr-blue hover:bg-vultr-sky-blue/80"
      >
        <Link href="/upload">Upload new docs</Link>
      </AppButton>
      <AppButton
        asChild
        variant="ghost"
        size="xs"
        className="rounded-[var(--radius-button)] border border-white/30 bg-white/10 px-4 py-2 text-white hover:border-white/50 hover:bg-white/20"
      >
        <Link href="/chat">Open vision chat</Link>
      </AppButton>
    </>
  );

  const heroMeta = !isReady ? (
    <HeroMetaGroup>
      <HeroMetaPill icon={AlertCircle} tone="warning">
        System not ready
      </HeroMetaPill>
    </HeroMetaGroup>
  ) : null;

  const handleImageOpen = (url: string, label?: string) => {
    if (!url) return;
    setLightboxSrc(url);
    setLightboxAlt(label ?? null);
    setLightboxOpen(true);
  };

  return (
    <>
      <RoutePageShell
        eyebrow="Services"
        title={
          <>
            <span className="bg-gradient-to-br from-white via-white to-white/70 bg-clip-text text-transparent">
              Search with Morty's
            </span>{" "}
            <span className="bg-gradient-to-r from-[#9ddfff] via-[#6fb5ff] to-[#9ddfff] bg-clip-text text-transparent">
              Visual Intelligence
            </span>
          </>
        }
        description="Ask Morty questions in natural language and let him surface the most relevant visual matches instantly."
        actions={heroActions}
        meta={heroMeta}
        innerClassName="space-y-6"
        variant="compact"
      >
        <motion.div
          className="flex h-full flex-col space-y-2"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, ease: "easeOut" }}
        >
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
                  placeholder="Ask Morty about content, visuals, or document details..."
                  className="input flex-1 border-none bg-transparent px-0 text-body shadow-none focus-visible:border-transparent focus-visible:ring-0 placeholder:text-white/70"
                  disabled={!isReady}
                />

                {/* Inline Search Button */}
                <div className="flex shrink-0 items-center gap-2">
                  <AppButton
                    variant="primary"
                    size="md"
                    elevated
                    disabled={loading || !isReady || !query.trim()}
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
                  </AppButton>
                </div>
              </div>
            </motion.div>

            {/* Settings Grid */}
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-2">
              <div className="rounded-xl border border-border/50 bg-card/50 p-3 backdrop-blur-sm">
                <label className="flex flex-col gap-2">
                  <span className="flex items-center gap-1 text-body-xs font-medium text-muted-foreground">
                    Top K
                    <InfoTooltip
                      description="Controls how many nearest neighbors the retriever fetches per query. Higher values surface more context but may add noise."
                      triggerAriaLabel="What is Top K?"
                    />
                  </span>
                  <input
                    type="number"
                    min={1}
                    value={k}
                    onChange={(event) => handleNumberChange(event, setK)}
                    className="input"
                  />
                </label>
              </div>
              <div className="rounded-xl border border-border/50 bg-card/50 p-3 backdrop-blur-sm">
                <div className="flex flex-col gap-2">
                  <span className="text-body-xs font-medium text-muted-foreground">Search Duration</span>
                  <div className="flex items-center gap-2 rounded-lg border border-border/50 bg-background px-3 py-2 text-body-sm">
                    <Clock className="size-icon-sm text-muted-foreground" />
                    <span className="font-medium">
                      {searchDurationMs !== null ? `${(searchDurationMs / 1000).toFixed(2)}s` : '-'}
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

          {/* Helper content before first search */}
          <AnimatePresence mode="wait">
            {!hasSearched && !loading && (
              <motion.section
                className="space-y-3 rounded-2xl border border-border/40 bg-card/30 p-4 backdrop-blur-sm"
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -16 }}
                transition={{ duration: 0.3 }}
              >
                <div className="flex items-center gap-2">
                  <Sparkles className="size-icon-xs text-primary" />
                  <h3 className="text-body font-bold">Ways to get started</h3>
                </div>

                <div className="grid gap-3 sm:grid-cols-3">
                  {SEARCH_HELPER_CARDS.map((card, index) => (
                    <motion.article
                      key={card.id}
                      className="group relative overflow-hidden rounded-xl border border-border/40 bg-background/70 p-4 transition-all hover:border-primary/50 hover:shadow-lg hover:shadow-primary/10"
                      initial={{ opacity: 0, y: 12 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.05, duration: 0.25 }}
                      whileHover={{ y: -4, scale: 1.01 }}
                      whileTap={{ scale: 0.99 }}
                    >
                      <div
                        className={`absolute inset-0 bg-gradient-to-br ${card.gradient} opacity-0 transition-opacity group-hover:opacity-10`}
                      />
                      <div className="relative space-y-3">
                        <div className="flex items-center gap-2">
                          <div className="flex size-10 items-center justify-center rounded-lg bg-muted/70">
                            <card.icon className="size-icon-xs text-primary" />
                          </div>
                          <h4 className="text-body-sm font-semibold">{card.title}</h4>
                        </div>
                        <p className="text-body-xs text-muted-foreground">{card.description}</p>
                        {card.href && card.actionLabel && (
                          <Link
                            href={card.href}
                            className="inline-flex items-center gap-1 text-body-xs font-semibold text-primary transition-colors hover:text-primary/80"
                          >
                            {card.actionLabel}
                            <ArrowRight className="size-icon-3xs" />
                          </Link>
                        )}
                      </div>
                    </motion.article>
                  ))}
                </div>

                <div className="rounded-xl border border-dashed border-border/30 bg-background/70 p-4 text-left">
                  <p className="text-body-xs font-semibold text-muted-foreground">Need inspiration?</p>
                  <div className="mt-2 flex flex-wrap gap-2">
                    {suggestedQueries.map((item) => (
                      <button
                        key={item}
                        type="button"
                        onClick={() => setQuery(item)}
                        className="inline-flex items-center gap-1 rounded-full border border-border/40 bg-background px-3 py-1 text-body-xs font-medium text-foreground transition-colors hover:border-primary/40 hover:text-primary"
                      >
                        <Clock className="size-icon-3xs text-primary/80" />
                        {item}
                      </button>
                    ))}
                  </div>
                </div>
              </motion.section>
            )}
          </AnimatePresence>

          {/* Results Section */}
          <AnimatePresence mode="wait">
            {(hasSearched || loading) && (
              <motion.div
                className="flex min-h-0 flex-1 flex-col"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.3 }}
              >
                {/* Results Header - Stats Only */}
                <div className="flex flex-wrap items-center justify-center gap-3">
                  {hasSearched && results.length > k && (
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
                          <AppButton
                            type="button"
                            onClick={clearResults}
                            size="xs"
                            variant="ghost"
                          >
                            <X className="size-icon-3xs" />
                            Clear
                          </AppButton>
                        </div>

                        <ScrollArea className="h-[40vh] w-full max-w-6xl mx-auto">
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
                                    <div className="relative h-18 w-18 shrink-0 overflow-hidden rounded-lg border border-border/50 bg-background/50">
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
                                      <h3 className="line-clamp-2 text-body-xs xs:text-body font-bold text-foreground">
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
      </RoutePageShell>
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
    </>
  );
}
