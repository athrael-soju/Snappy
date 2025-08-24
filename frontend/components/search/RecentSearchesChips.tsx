"use client";

import React from "react";
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
  if (!visible || recentSearches.length === 0) return null;
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
        <div className="overflow-x-auto [-ms-overflow-style:none] [scrollbar-width:none] no-scrollbar">
          <div className="flex items-center gap-2 pr-1 whitespace-nowrap">
            {recentSearches.map((search, idx) => (
              <div key={idx} className="inline-flex items-center gap-1 px-3 py-1 text-sm bg-muted/50 hover:bg-blue-100 rounded-full transition-colors">
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
