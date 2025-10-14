"use client";

import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { Search, Loader2, Trash2 } from "lucide-react";
import { ChatSettings } from "@/components/chat-settings";
import RecentSearchesChips from "./RecentSearchesChips";

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
  const showRecentSearches = !hasResults && recentSearches.length > 0;

  return (
    <form onSubmit={onSubmit} className="flex flex-col gap-4" aria-labelledby="search-heading">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
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
            className="h-14 rounded-2xl border border-input bg-card pl-12 pr-4 text-base shadow-sm transition focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background disabled:opacity-70"
          />
        </div>
        <div className="flex w-full flex-col gap-2 sm:w-auto sm:flex-row sm:items-center sm:justify-end">
          <div className="flex w-full items-center justify-between gap-2 rounded-xl border border-input bg-secondary/40 px-3 py-2 shadow-sm sm:w-auto sm:justify-center sm:px-2 sm:py-1">
            <div className="flex items-center gap-2">
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
                <TooltipContent sideOffset={8} className="bg-popover text-popover-foreground">
                  Search settings
                </TooltipContent>
              </Tooltip>
              <span className="text-xs font-medium text-muted-foreground sm:hidden">Settings</span>
            </div>

            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  type="button"
                  onClick={onClear}
                  disabled={loading || !hasResults}
                  variant="ghost"
                  className="h-12 flex-1 justify-center rounded-lg text-sm font-medium sm:flex-none sm:h-12 sm:w-12 sm:rounded-md"
                >
                  <Trash2 className="h-5 w-5" />
                  <span className="ml-2 sm:hidden">Clear</span>
                </Button>
              </TooltipTrigger>
              <TooltipContent sideOffset={8} className="bg-popover text-popover-foreground">
                <p>{hasResults ? "Clear results" : "No results to clear"}</p>
              </TooltipContent>
            </Tooltip>
          </div>

          <Button
            type="submit"
            disabled={loading || !q.trim()}
            size="lg"
            className="h-14 w-full rounded-2xl px-6 text-base font-semibold sm:w-auto"
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

      {/* Recent Searches */}
      <RecentSearchesChips
        recentSearches={recentSearches}
        loading={loading}
        visible={showRecentSearches}
        onSelect={(q) => onSelectRecent?.(q)}
        onRemove={(q) => onRemoveRecent?.(q)}
      />

      {filtersSlot && (
        <div className="flex flex-wrap items-center gap-2" role="group" aria-label="Search filters">
          {filtersSlot}
        </div>
      )}
    </form>
  );
}

