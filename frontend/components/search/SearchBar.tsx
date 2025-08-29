"use client";

import React from "react";
import { Input } from "@/components/ui/8bit/input";
import { Button } from "@/components/ui/8bit/button";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/8bit/tooltip";
import { Search, Loader2 } from "lucide-react";
import { ChatSettings } from "@/components/chat-settings";

export interface SearchBarProps {
  q: string;
  setQ: (v: string) => void;
  loading: boolean;
  onSubmit: (e: React.FormEvent) => void;
  k: number;
  setK: (k: number) => void;
}

export default function SearchBar({ q, setQ, loading, onSubmit, k, setK }: SearchBarProps) {
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
              className="text-base sm:text-lg pl-14 h-14 sm:h-16 rounded-2xl border-2 shadow-md bg-card placeholder:text-muted-foreground/80 focus-visible:ring-2 focus-visible:ring-ring focus-visible:border-ring focus:shadow-lg"
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
            <Button
              type="submit"
              disabled={loading || !q.trim()}
              size="lg"
              className="h-14 px-8 rounded-2xl bg-primary text-primary-foreground hover:bg-primary/90 focus:ring-2 focus:ring-offset-2 focus:ring-ring shadow"
            >
              {loading ? (
                <>
                  <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                  Searching...
                </>
              ) : (
                <>
                  <Search className="w-5 h-5 mr-2" />
                  Search
                </>
              )}
            </Button>
          </div>
        </div>
      </div>
    </form>
  );
}
