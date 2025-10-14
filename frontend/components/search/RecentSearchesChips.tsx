"use client";

import { Clock, X } from "lucide-react";
import { AnimatePresence, motion } from "framer-motion";

import { ScrollArea, ScrollBar } from "@/components/ui/scroll-area";

export interface RecentSearchesChipsProps {
  recentSearches: string[];
  loading?: boolean;
  visible?: boolean;
  onSelect: (q: string) => void;
  onRemove: (q: string) => void;
}

export default function RecentSearchesChips({
  recentSearches,
  loading = false,
  visible = true,
  onSelect,
  onRemove,
}: RecentSearchesChipsProps) {
  if (!visible || recentSearches.length === 0) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, height: 0 }}
        animate={{ opacity: 1, height: "auto" }}
        exit={{ opacity: 0, height: 0 }}
        className="space-y-3"
      >
        <div className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
          <Clock className="h-4 w-4" />
          <span>Recent searches</span>
        </div>

        <ScrollArea className="-mx-2">
          <div className="flex w-max gap-2 px-2 pb-1">
            {recentSearches.map((search) => (
              <Chip
                key={search}
                label={search}
                disabled={loading}
                onClick={() => onSelect(search)}
                onRemove={() => onRemove(search)}
              />
            ))}
          </div>
          <ScrollBar orientation="horizontal" />
        </ScrollArea>
      </motion.div>
    </AnimatePresence>
  );
}

function Chip({
  label,
  disabled,
  onClick,
  onRemove,
}: {
  label: string;
  disabled?: boolean;
  onClick: () => void;
  onRemove: () => void;
}) {
  return (
    <span className="inline-flex min-w-0 items-center overflow-hidden rounded-full border border-input bg-card/80 text-sm shadow-sm">
      <button
        type="button"
        onClick={onClick}
        disabled={disabled}
        className="max-w-[14rem] truncate px-3 py-1.5 text-left text-sm text-foreground transition hover:bg-secondary/70 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        title={label}
      >
        {label}
      </button>
      <button
        type="button"
        onClick={onRemove}
        disabled={disabled}
        className="flex h-full items-center justify-center px-2 text-muted-foreground transition hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-destructive"
        aria-label={`Remove ${label}`}
      >
        <X className="h-3.5 w-3.5" />
      </button>
    </span>
  );
}
