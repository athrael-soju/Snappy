"use client";

import React, { useRef, useEffect, useState } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { Search, Loader2, Trash2, Clock, ChevronLeft, ChevronRight, X } from "lucide-react";
import { ChatSettings } from "@/components/chat-settings";
import { AnimatePresence, motion } from "framer-motion";

export interface SearchBarProps {
  q: string;
  setQ: (v: string) => void;
  loading: boolean;
  onSubmit: (e: React.FormEvent) => void;
  k: number;
  setK: (k: number) => void;
  topK?: number;
  setTopK?: (v: number) => void;
  onClear: () => void;
  hasResults?: boolean;
  inputRef?: React.RefObject<HTMLInputElement>;
  filtersSlot?: React.ReactNode;
  recentSearches?: string[];
  onSelectRecent?: (q: string) => void;
  onRemoveRecent?: (q: string) => void;
}

export default function SearchBar({
  q,
  setQ,
  loading,
  onSubmit,
  k,
  setK,
  topK = 16,
  setTopK,
  onClear,
  hasResults = false,
  inputRef,
  filtersSlot,
  recentSearches = [],
  onSelectRecent,
  onRemoveRecent,
}: SearchBarProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [currentPage, setCurrentPage] = useState(0);
  const [atStart, setAtStart] = useState(true);
  const [atEnd, setAtEnd] = useState(false);

  // Enforce a maximum of 9 items and pre-compute pages of 3
  const items = recentSearches.slice(0, 9);
  const pages: string[][] = [];
  for (let i = 0; i < items.length; i += 3) {
    pages.push(items.slice(i, i + 3));
  }
  const pagesLength = pages.length;

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const onWheel = (e: WheelEvent) => {
      if (Math.abs(e.deltaY) > Math.abs(e.deltaX) && !e.shiftKey) {
        e.preventDefault();
        const pageWidth = el.clientWidth;
        const direction = e.deltaY > 0 ? 1 : -1;
        const scrolledPage = Math.round(el.scrollLeft / pageWidth);
        const newPage = Math.max(0, Math.min(scrolledPage + direction, pagesLength - 1));
        el.scrollTo({ left: newPage * pageWidth, behavior: 'smooth' });
        setCurrentPage(newPage);
        setAtStart(newPage === 0);
        setAtEnd(newPage >= pagesLength - 1);
      }
    };
    const onScroll = () => {
      const pageWidth = el.clientWidth;
      const page = Math.round(el.scrollLeft / pageWidth);
      setCurrentPage(page);
      setAtStart(page === 0);
      setAtEnd(page >= pagesLength - 1);
    };
    el.addEventListener('wheel', onWheel, { passive: false });
    el.addEventListener('scroll', onScroll);
    return () => {
      el.removeEventListener('wheel', onWheel);
      el.removeEventListener('scroll', onScroll);
    };
  }, [pagesLength]);

  const scrollByPage = (direction: 1 | -1) => {
    const el = containerRef.current;
    if (!el) return;
    const pageWidth = el.clientWidth;
    const nextPage = Math.max(0, Math.min(currentPage + direction, pagesLength - 1));
    el.scrollTo({ left: nextPage * pageWidth, behavior: 'smooth' });
    setCurrentPage(nextPage);
    setAtStart(nextPage === 0);
    setAtEnd(nextPage >= pagesLength - 1);
  };

  const goToPage = (index: number) => {
    const el = containerRef.current;
    if (!el) return;
    const target = Math.max(0, Math.min(index, pagesLength - 1));
    const pageWidth = el.clientWidth;
    el.scrollTo({ left: target * pageWidth, behavior: 'smooth' });
    setCurrentPage(target);
    setAtStart(target === 0);
    setAtEnd(target >= pagesLength - 1);
  };

  const showRecentSearches = !hasResults && recentSearches.length > 0;

  return (
    <form onSubmit={onSubmit} className="flex flex-col gap-4" aria-labelledby="search-heading">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
        <div className="relative flex-1">
          <Search className="pointer-events-none absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-muted-foreground" />
          <Input
            ref={inputRef}
            placeholder="Describe the document or image you need..."
            value={q}
            onChange={(e) => setQ(e.target.value)}
            required
            disabled={loading}
            aria-label="Search query"
            className="h-14 rounded-2xl border border-muted bg-[color:var(--surface-0)]/95 pl-12 pr-24 text-base shadow-[var(--shadow-1)] transition focus-visible:border-ring focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-[color:var(--surface-0)] disabled:opacity-70"
          />
        </div>
        <div className="flex items-stretch justify-end gap-2 self-stretch">
          <div className="flex items-center gap-2 rounded-2xl border border-muted bg-[color:var(--surface-1)]/80 px-2 py-1 shadow-[var(--shadow-1)]">
            <Tooltip>
              <TooltipTrigger asChild>
                <div>
                  <ChatSettings
                    k={k}
                    setK={setK}
                    loading={loading}
                    className="h-12 w-12"
                    topK={topK}
                    setTopK={setTopK}
                    showMaxTokens={false}
                  />
                </div>
              </TooltipTrigger>
              <TooltipContent sideOffset={8}>Search settings</TooltipContent>
            </Tooltip>

            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  type="button"
                  onClick={onClear}
                  disabled={loading || !hasResults}
                  size="icon"
                  variant="ghost"
                  className="h-12 w-12 rounded-xl text-muted-foreground hover:bg-[color:var(--surface-2)] hover:text-foreground focus-visible:ring-2 focus-visible:ring-ring/40 disabled:opacity-50"
                >
                  <Trash2 className="h-5 w-5" />
                </Button>
              </TooltipTrigger>
              <TooltipContent sideOffset={8}>
                <p>{hasResults ? "Clear results" : "No results to clear"}</p>
              </TooltipContent>
            </Tooltip>
          </div>

          <Button
            type="submit"
            disabled={loading || !q.trim()}
            className="h-14 rounded-2xl bg-primary px-5 text-base font-semibold text-primary-foreground shadow-[var(--shadow-2)] transition hover:bg-primary/90 focus-visible:ring-2 focus-visible:ring-ring/40 focus-visible:ring-offset-2 focus-visible:ring-offset-[color:var(--surface-0)] disabled:opacity-70"
          >
            {loading ? (
              <>
                <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                Searching
              </>
            ) : (
              <>
                <Search className="mr-2 h-5 w-5" />
                Search
              </>
            )}
          </Button>
        </div>
      </div>

      {/* Recent Searches - integrated */}
      <AnimatePresence>
        {showRecentSearches && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="space-y-2"
          >
            <div className="flex items-center gap-2">
              <Clock className="w-3.5 h-3.5 text-muted-foreground" />
              <span className="text-xs font-medium text-muted-foreground">Recent searches</span>
            </div>
            <div className="relative">
              {/* Left chevron */}
              <button
                type="button"
                aria-label="Previous"
                onClick={() => scrollByPage(-1)}
                disabled={currentPage === 0}
                className="absolute left-0 top-1/2 -translate-y-1/2 z-10 rounded-md border border-muted bg-[color:var(--surface-0)]/90 p-1 text-muted-foreground transition hover:bg-[color:var(--surface-2)] hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/35 disabled:cursor-not-allowed disabled:opacity-40"
              >
                <ChevronLeft className="w-3.5 h-3.5" />
              </button>

              {/* Right chevron */}
              <button
                type="button"
                aria-label="Next"
                onClick={() => scrollByPage(1)}
                disabled={currentPage >= pages.length - 1}
                className="absolute right-1 top-1/2 -translate-y-1/2 z-10 rounded-md border border-muted bg-[color:var(--surface-0)]/90 p-1 text-muted-foreground transition hover:bg-[color:var(--surface-2)] hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/35 disabled:cursor-not-allowed disabled:opacity-40"
              >
                <ChevronRight className="w-3.5 h-3.5" />
              </button>

              <div
                ref={containerRef}
                className="overflow-x-hidden overflow-y-visible snap-x snap-mandatory"
              >
                <div className="flex w-full">
                  {pages.map((page, pIdx) => (
                    <div key={pIdx} className="shrink-0 w-full snap-start px-8 py-0.5 overflow-visible">
                      <div className="flex items-stretch gap-2 pr-1 overflow-visible">
                        {page.map((search, idx) => (
                          <motion.div
                            key={`${pIdx}-${idx}`}
                            whileHover={{ scale: 1.02, y: -2 }}
                            whileTap={{ scale: 0.98 }}
                            className="relative flex-1 min-w-0 rounded-lg border border-muted bg-[color:var(--surface-1)]/70 p-2 text-xs transition-all group transform-gpu will-change-transform hover:border-primary/40 hover:bg-primary/10 focus-within:border-primary/50 focus-within:ring-2 focus-within:ring-ring/30"
                          >
                            <button
                              type="button"
                              onClick={() => onSelectRecent?.(search)}
                              disabled={!!loading}
                              className="text-left focus:outline-none min-w-0 h-full block pr-6 w-full"
                            >
                              <div className="flex items-center gap-2">
                                <div className="p-1 bg-muted rounded group-hover:bg-muted transition-colors shrink-0">
                                  <Clock className="w-3 h-3 text-muted-foreground" />
                                </div>
                                <span
                                  className="block group-hover:text-foreground transition-colors text-muted-foreground line-clamp-1"
                                >
                                  {search}
                                </span>
                              </div>
                            </button>
                            <button
                              type="button"
                              aria-label={`Remove ${search}`}
                              onClick={() => onRemoveRecent?.(search)}
                              className="absolute top-0.5 right-0.5 rounded-full p-0.5 text-muted-foreground transition hover:bg-[color:var(--surface-2)] hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/35"
                              disabled={!!loading}
                            >
                              <X className="w-3 h-3 text-muted-foreground" />
                            </button>
                          </motion.div>
                        ))}
                        {/* Fill remaining slots to keep 3 columns aligned */}
                        {Array.from({ length: Math.max(0, 3 - page.length) }).map((_, i) => (
                          <div key={`empty-${pIdx}-${i}`} className="flex-1" />
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Edge gradients as scroll hints */}
              {!atStart && (
                <div
                  aria-hidden
                  className="pointer-events-none absolute left-0 top-0 h-full w-8 bg-gradient-to-r from-[color:var(--surface-0)] to-transparent"
                />
              )}
              {!atEnd && (
                <div
                  aria-hidden
                  className="pointer-events-none absolute right-0 top-0 h-full w-8 bg-gradient-to-l from-[color:var(--surface-0)] to-transparent"
                />
              )}
            </div>

            {/* Pagination dots */}
            {pagesLength > 1 && (
              <div className="mt-1 flex items-center justify-center gap-1" aria-label="Carousel pagination">
                {Array.from({ length: pagesLength }).map((_, i) => (
                  <button
                    key={i}
                    type="button"
                    aria-label={`Go to page ${i + 1}`}
                    onClick={() => goToPage(i)}
                    className={`h-1 rounded-full transition-all ${i === currentPage ? 'w-3 bg-foreground' : 'w-1.5 bg-muted-foreground/40'}`}
                  />
                ))}
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>

      {filtersSlot && (
        <div className="flex flex-wrap items-center gap-2" role="group" aria-label="Search filters">
          {filtersSlot}
        </div>
      )}
    </form>
  );
}

