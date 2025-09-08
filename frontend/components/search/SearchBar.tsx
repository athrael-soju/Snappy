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
  onClear: () => void;
  hasResults?: boolean; // Whether there are actual results to clear
}

export default function SearchBar({ q, setQ, loading, onSubmit, k, setK, onClear, hasResults = false }: SearchBarProps) {
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
              className="text-base sm:text-lg pl-14 h-14 sm:h-16 rounded-2xl border-2 shadow-md bg-background placeholder:text-muted-foreground/80 focus-visible:ring-2 focus-visible:ring-primary focus-visible:border-primary focus:shadow-lg"
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
                  className="h-14 w-14 rounded-2xl bg-gradient-to-r from-primary to-primary hover:from-primary/90 hover:to-primary/90 text-primary-foreground focus:ring-2 focus:ring-offset-2 focus:ring-primary shadow"
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
                  className="h-14 w-14 rounded-2xl border-2 border-border hover:border-primary hover:bg-gradient-to-r hover:from-primary/10 hover:to-primary/10 text-muted-foreground hover:text-primary transition-all duration-300 shadow-sm hover:shadow-md disabled:opacity-50"
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
