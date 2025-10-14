"use client";

import React, { useRef } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Tooltip, TooltipContent, TooltipTrigger, TooltipProvider } from "@/components/ui/tooltip";
import { Search, Loader2, Trash2 } from "lucide-react";
import { ChatSettings } from "@/components/chat-settings";

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
}: SearchBarProps) {

  return (
    <TooltipProvider>
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
              className="h-14 rounded-xl border pl-12 text-base bg-background/50 backdrop-blur-sm transition-all duration-300 focus:bg-background/80"
            />
          </div>
          <div className="flex items-center gap-2">
            <div className="flex items-center gap-2 rounded-xl border bg-card/50 backdrop-blur-sm p-2">
              <Tooltip>
                <TooltipTrigger asChild>
                  <div>
                    <ChatSettings
                      k={k}
                      setK={setK}
                      loading={loading}
                      className="h-10 w-10"
                      topK={topK}
                      setTopK={setTopK}
                      showMaxTokens={false}
                    />
                  </div>
                </TooltipTrigger>
                <TooltipContent>Search settings</TooltipContent>
              </Tooltip>

              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    type="button"
                    onClick={onClear}
                    disabled={loading || !hasResults}
                    size="icon"
                    variant="ghost"
                    className="h-10 w-10"
                  >
                    <Trash2 className="h-5 w-5" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>
                  {hasResults ? "Clear results" : "No results to clear"}
                </TooltipContent>
              </Tooltip>
            </div>

          <Button
            type="submit"
            disabled={loading || !q.trim()}
            className="h-14 rounded-xl px-6"
            size="lg"
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

        {filtersSlot && (
          <div className="flex flex-wrap items-center gap-2" role="group" aria-label="Search filters">
            {filtersSlot}
          </div>
        )}
      </form>
    </TooltipProvider>
  );
}

