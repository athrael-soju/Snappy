"use client";

import React from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { Search, Loader2 } from "lucide-react";
import { ChatSettings } from "@/components/chat-settings";
import type { KMode } from "@/components/chat-settings";

export interface SearchBarProps {
  q: string;
  setQ: (v: string) => void;
  loading: boolean;
  onSubmit: (e: React.FormEvent) => void;
  k: number;
  kMode: KMode;
  setK: (k: number) => void;
  setKMode: (m: KMode) => void;
}

export default function SearchBar({ q, setQ, loading, onSubmit, k, kMode, setK, setKMode }: SearchBarProps) {
  return (
    <form onSubmit={onSubmit} className="space-y-4">
      <div className="space-y-3">
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-muted-foreground" />
            <Input
              placeholder="Try: 'Find invoices with company logo' or 'Show charts with sales data'"
              value={q}
              onChange={(e) => setQ(e.target.value)}
              required
              disabled={loading}
              aria-label="Search query"
              className="text-base pl-11 h-12 border-2 focus:border-blue-500 bg-white placeholder:text-muted-foreground/80"
            />
          </div>
          <div className="flex items-center gap-2">
            <Tooltip>
              <TooltipTrigger asChild>
                <div>
                  <ChatSettings
                    k={k}
                    kMode={kMode}
                    setK={setK}
                    setKMode={setKMode}
                    loading={loading}
                    className="h-12 w-12"
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
              className="h-12 px-6 bg-gradient-to-r from-blue-700 to-cyan-700 hover:from-blue-800 hover:to-cyan-800 text-white focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
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
