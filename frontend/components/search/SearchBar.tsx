"use client";

import React from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
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
  hasResults?: boolean; // Whether there are actual results to clear
}

export default function SearchBar({ q, setQ, loading, onSubmit, k, setK, topK = 16, setTopK, onClear, hasResults = false }: SearchBarProps) {
  return (
    <form onSubmit={onSubmit} className="space-y-4 mx-auto max-w-4xl">
      <div className="space-y-3">
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="flex-1 relative">
            <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 w-6 h-6 text-muted-foreground" />
            <Input
              placeholder="Search by text or even describe the image/document you need."
              value={q}
              onChange={(e) => setQ(e.target.value)}
              required
              disabled={loading}
              aria-label="Search query"
              className="text-base sm:text-lg pl-14 h-14 sm:h-16 rounded-2xl border-2 shadow-md bg-white placeholder:text-muted-foreground/80 focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:border-blue-500 focus:shadow-lg"
            />
          </div>
          <div className="flex items-center gap-2">
            <Tooltip>
              <TooltipTrigger asChild>
                <div>
                  <ChatSettings
                    k={k}
                    setK={setK}
                    loading={loading}
                    className="h-14 w-14"
                    topK={topK}
                    setTopK={setTopK}
                    showMaxTokens={false}
                  />
                </div>
              </TooltipTrigger>
              <TooltipContent>
                <p>Search settings</p>
              </TooltipContent>
            </Tooltip>
            
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  type="submit"
                  disabled={loading || !q.trim()}
                  size="icon"
                  className="h-14 w-14 rounded-2xl bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-700 hover:to-cyan-700 text-white shadow-lg hover:shadow-xl transition-all duration-300"
                >
                  {loading ? (
                    <Loader2 className="w-6 h-6 animate-spin" />
                  ) : (
                    <Search className="w-6 h-6" />
                  )}
                </Button>
              </TooltipTrigger>
              <TooltipContent>
                <p>{loading ? 'Searching...' : 'Search documents'}</p>
              </TooltipContent>
            </Tooltip>
            
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  type="button"
                  onClick={onClear}
                  disabled={loading || !hasResults}
                  size="icon"
                  variant="outline"
                  className="h-14 w-14 rounded-2xl border-2 border-blue-200/50 hover:border-blue-400 hover:bg-gradient-to-r hover:from-blue-50 hover:to-cyan-50 text-muted-foreground hover:text-blue-600 transition-all duration-300 shadow-md hover:shadow-lg disabled:opacity-50"
                >
                  <Trash2 className="w-5 h-5" />
                </Button>
              </TooltipTrigger>
              <TooltipContent>
                <p>{hasResults ? 'Clear search results' : 'No results to clear'}</p>
              </TooltipContent>
            </Tooltip>
          </div>
        </div>
      </div>
    </form>
  );
}
