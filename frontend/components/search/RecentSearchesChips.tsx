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
      }
    }
    const onScroll = () => {
      const pageWidth = el.clientWidth
      const page = Math.round(el.scrollLeft / pageWidth)
      setCurrentPage(page)
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
          <Clock className="w-4 h-4 text-primary" />
          <span className="text-sm font-medium text-muted-foreground">Recent searches:</span>
        </div>
        <div className="relative">
          {/* Left chevron */}
          <button
            type="button"
            aria-label="Previous"
            onClick={() => scrollByPage(-1)}
            disabled={currentPage === 0}
            className="absolute left-0 top-1/2 -translate-y-1/2 z-10 p-1.5 rounded-md bg-card/80 backdrop-blur-sm text-muted-foreground hover:text-primary hover:bg-primary/10 shadow ring-1 ring-border disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>

          {/* Right chevron */}
          <button
            type="button"
            aria-label="Next"
            onClick={() => scrollByPage(1)}
            disabled={currentPage >= pages.length - 1}
            className="absolute right-0 top-1/2 -translate-y-1/2 z-10 p-1.5 rounded-md bg-card/80 backdrop-blur-sm text-muted-foreground hover:text-primary hover:bg-primary/10 shadow ring-1 ring-border disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
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
                        className="relative flex-1 min-w-0 p-3 text-sm rounded-xl border-2 border-dashed border-primary/30 hover:border-primary hover:bg-primary/10 hover:shadow-sm transition-all group min-h-[3rem] transform-gpu will-change-transform"
                      >
                        <button
                          onClick={() => onSelect(search)}
                          disabled={!!loading}
                          className="text-left focus:outline-none min-w-0 h-full block pr-7"
                        >
                          <div className="flex items-start gap-3">
                            <div className="p-1.5 bg-primary/10 rounded-lg group-hover:bg-primary/20 transition-colors">
                              <Clock className="w-4 h-4 text-primary" />
                            </div>
                            <span
                              className="block group-hover:text-primary transition-colors"
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
                          className="absolute top-1 right-1 rounded-full hover:bg-primary/10 p-0.5"
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
        </div>
      </motion.div>
    </AnimatePresence>
  );
}
