"use client";

import React, { useRef, useEffect } from "react";
import { X, Clock } from "lucide-react";
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

  useEffect(() => {
    const el = containerRef.current
    if (!el) return
    const onWheel = (e: WheelEvent) => {
      // If the user scrolls vertically, translate to horizontal scroll for this row
      if (Math.abs(e.deltaY) > Math.abs(e.deltaX) && !e.shiftKey) {
        e.preventDefault()
        el.scrollLeft += e.deltaY
      }
    }
    el.addEventListener('wheel', onWheel, { passive: false })
    return () => el.removeEventListener('wheel', onWheel)
  }, [])

  if (!visible || recentSearches.length === 0) return null;
  const items = recentSearches.slice(0, 10)

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
        <div
          ref={containerRef}
          className="overflow-x-auto [-ms-overflow-style:none] [scrollbar-width:none] no-scrollbar snap-x snap-mandatory"
        >
          <div className="flex items-center gap-2 pr-1 whitespace-nowrap">
            {items.map((search, idx) => (
              <div
                key={idx}
                className="inline-flex items-center gap-1 px-3 py-1 text-sm bg-muted/50 hover:bg-blue-100 rounded-full transition-colors snap-start"
              >
                <button
                  onClick={() => onSelect(search)}
                  disabled={!!loading}
                  className="focus:outline-none"
                >
                  {search}
                </button>
                <button
                  aria-label={`Remove ${search}`}
                  onClick={() => onRemove(search)}
                  className="rounded-full hover:bg-muted p-0.5"
                  disabled={!!loading}
                >
                  <X className="w-3.5 h-3.5 text-muted-foreground" />
                </button>
              </div>
            ))}
          </div>
        </div>
      </motion.div>
    </AnimatePresence>
  );
}
