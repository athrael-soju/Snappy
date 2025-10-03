"use client";

import React, { useRef, useEffect, useState } from "react";
import { X, Clock, ChevronLeft, ChevronRight } from "lucide-react";
import { AnimatePresence, motion } from "framer-motion";

export interface RecentSearchesChipsProps {
  recentSearches: string[];
  loading?: boolean;
  visible?: boolean;
  onSelect: (q: string) => void;
  onRemove: (q: string) => void;
}

export default function RecentSearchesChips({ recentSearches, loading, visible = true, onSelect, onRemove }: RecentSearchesChipsProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const [currentPage, setCurrentPage] = useState(0)
  const [atStart, setAtStart] = useState(true)
  const [atEnd, setAtEnd] = useState(false)

  // Enforce a maximum of 9 items and pre-compute pages of 3
  const items = recentSearches.slice(0, 9)
  const pages: string[][] = []
  for (let i = 0; i < items.length; i += 3) {
    pages.push(items.slice(i, i + 3))
  }
  const pagesLength = pages.length

  useEffect(() => {
    const el = containerRef.current
    if (!el) return
    const onWheel = (e: WheelEvent) => {
      // Convert vertical wheel to page-based horizontal scroll (3 items/page)
      if (Math.abs(e.deltaY) > Math.abs(e.deltaX) && !e.shiftKey) {
        e.preventDefault()
        const pageWidth = el.clientWidth
        const direction = e.deltaY > 0 ? 1 : -1
        const scrolledPage = Math.round(el.scrollLeft / pageWidth)
        const newPage = Math.max(0, Math.min(scrolledPage + direction, pagesLength - 1))
        el.scrollTo({ left: newPage * pageWidth, behavior: 'smooth' })
        setCurrentPage(newPage)
        setAtStart(newPage === 0)
        setAtEnd(newPage >= pagesLength - 1)
      }
    }
    const onScroll = () => {
      const pageWidth = el.clientWidth
      const page = Math.round(el.scrollLeft / pageWidth)
      setCurrentPage(page)
      setAtStart(page === 0)
      setAtEnd(page >= pagesLength - 1)
    }
    el.addEventListener('wheel', onWheel, { passive: false })
    el.addEventListener('scroll', onScroll)
    return () => {
      el.removeEventListener('wheel', onWheel)
      el.removeEventListener('scroll', onScroll)
    }
  }, [pagesLength])

  if (!visible || recentSearches.length === 0) return null;

  const scrollByPage = (direction: 1 | -1) => {
    const el = containerRef.current
    if (!el) return
    const pageWidth = el.clientWidth
    const nextPage = Math.max(0, Math.min(currentPage + direction, pagesLength - 1))
    el.scrollTo({ left: nextPage * pageWidth, behavior: 'smooth' })
    setCurrentPage(nextPage)
    setAtStart(nextPage === 0)
    setAtEnd(nextPage >= pagesLength - 1)
  }

  const goToPage = (index: number) => {
    const el = containerRef.current
    if (!el) return
    const target = Math.max(0, Math.min(index, pagesLength - 1))
    const pageWidth = el.clientWidth
    el.scrollTo({ left: target * pageWidth, behavior: 'smooth' })
    setCurrentPage(target)
    setAtStart(target === 0)
    setAtEnd(target >= pagesLength - 1)
  }

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, height: 0 }}
        animate={{ opacity: 1, height: "auto" }}
        exit={{ opacity: 0, height: 0 }}
        className="space-y-3"
      >
        <div className="flex items-center gap-2">
          <Clock className="w-4 h-4 text-muted-foreground" />
          <span className="text-sm font-medium text-muted-foreground">Recent searches:</span>
        </div>
        {/* Wrap scroller and arrows in a relative container so arrows center to the row, not including dots */}
        <div className="relative">
          {/* Left chevron */}
          <button
            type="button"
            aria-label="Previous"
            onClick={() => scrollByPage(-1)}
            disabled={currentPage === 0}
            className="absolute left-0 top-1/2 -translate-y-1/2 z-10 p-1.5 rounded-md bg-card/80 backdrop-blur-sm text-muted-foreground hover:text-foreground hover:bg-muted shadow ring-1 ring-border disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>

          {/* Right chevron */}
          <button
            type="button"
            aria-label="Next"
            onClick={() => scrollByPage(1)}
            disabled={currentPage >= pages.length - 1}
            className="absolute right-1 top-1/2 -translate-y-1/2 z-10 p-1.5 rounded-md bg-card/80 backdrop-blur-sm text-muted-foreground hover:text-foreground hover:bg-muted shadow ring-1 ring-border disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            <ChevronRight className="w-4 h-4" />
          </button>

          <div
            ref={containerRef}
            className="overflow-x-hidden overflow-y-visible snap-x snap-mandatory"
          >
            <div className="flex w-full">
              {pages.map((page, pIdx) => (
                <div key={pIdx} className="shrink-0 w-full snap-start px-8 py-1 overflow-visible">
                  <div className="flex items-stretch gap-2 pr-1 overflow-visible">
                    {page.map((search, idx) => (
                      <motion.div
                        key={`${pIdx}-${idx}`}
                        whileHover={{ scale: 1.02, y: -2 }}
                        whileTap={{ scale: 0.98 }}
                        className="relative flex-1 min-w-0 p-3 text-sm rounded-xl border-2 border-dashed border-border hover:border-foreground/40 hover:bg-muted hover:shadow-sm transition-all group min-h-[3rem] transform-gpu will-change-transform"
                      >
                        <button
                          onClick={() => onSelect(search)}
                          disabled={!!loading}
                          className="text-left focus:outline-none min-w-0 h-full block pr-7"
                        >
                          <div className="flex items-start gap-3">
                            <div className="p-1.5 bg-muted rounded-lg group-hover:bg-muted transition-colors">
                              <Clock className="w-4 h-4 text-muted-foreground" />
                            </div>
                            <span
                              className="block group-hover:text-foreground transition-colors"
                              style={{
                                display: '-webkit-box',
                                WebkitLineClamp: 2,
                                WebkitBoxOrient: 'vertical' as any,
                                overflow: 'hidden',
                                textOverflow: 'ellipsis',
                                lineHeight: '1.2rem',
                              }}
                            >
                              {search}
                            </span>
                          </div>
                        </button>
                        <button
                          aria-label={`Remove ${search}`}
                          onClick={() => onRemove(search)}
                          className="absolute top-1 right-1 rounded-full hover:bg-muted p-0.5"
                          disabled={!!loading}
                        >
                          <X className="w-3.5 h-3.5 text-muted-foreground" />
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
              className="pointer-events-none absolute left-0 top-0 h-full w-8 from-background to-transparent"
            />
          )}
          {!atEnd && (
            <div
              aria-hidden
              className="pointer-events-none absolute right-0 top-0 h-full w-8 from-background to-transparent"
            />
          )}

        </div>

        {/* Pagination dots */}
        {pagesLength > 1 && (
          <div className="mt-2 flex items-center justify-center gap-1.5" aria-label="Carousel pagination">
            {Array.from({ length: pagesLength }).map((_, i) => (
              <button
                key={i}
                type="button"
                aria-label={`Go to page ${i + 1}`}
                onClick={() => goToPage(i)}
                className={`h-1.5 rounded-full transition-all ${i === currentPage ? 'w-4 bg-foreground' : 'w-2 bg-muted-foreground/40'}`}
              />
            ))}
          </div>
        )}
      </motion.div>
    </AnimatePresence>
  );
}
