"use client";

import { ChangeEvent, FormEvent, useMemo, useState } from "react";
import "@/lib/api/client";
import Image from "next/image";
import { Search, Loader2, X, AlertCircle, Sparkles, ArrowRight, FileText, Clock } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { RetrievalService } from "@/lib/api/generated";
import { parseSearchResults } from "@/lib/api/runtime";
import { useSearchStore } from "@/lib/hooks/use-search-store";
import { useSystemStatus } from "@/stores/app-store";

const suggestedQueries = [
  "Show recent upload summaries",
  "Find diagrams about the architecture",
  "Which contracts mention service levels?",
];

export default function SearchPage() {
  const {
    query,
    setQuery,
    results,
    hasSearched,
    searchDurationMs,
    k,
    setK,
    topK,
    setTopK,
    reset,
    setResults,
    setHasSearched,
  } = useSearchStore();
  const { isReady } = useSystemStatus();

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const truncatedResults = useMemo(() => results.slice(0, topK), [results, topK]);

  const handleNumberChange = (event: ChangeEvent<HTMLInputElement>, setter: (value: number) => void) => {
    const next = Number.parseInt(event.target.value, 10);
    if (!Number.isNaN(next)) {
      setter(next);
    }
  };

  const handleSearch = async (event: FormEvent) => {
    event.preventDefault();
    const trimmed = query.trim();
    if (!trimmed) {
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const start = performance.now();
      const data = await RetrievalService.searchSearchGet(trimmed, k);
      const parsed = parseSearchResults(data);
      setResults(parsed, performance.now() - start);
      setHasSearched(true);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Search failed";
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  const clearResults = () => {
    reset();
    setError(null);
  };

  return (
    <div className="relative flex h-full min-h-full flex-col overflow-hidden">
      <div className="flex h-full flex-1 flex-col overflow-hidden px-4 py-6 sm:px-6 lg:px-8">
        <div className="mx-auto flex h-full w-full max-w-5xl flex-col space-y-4">
          {/* Header Section */}
          <div className="shrink-0 space-y-2 text-center">
            <h1 className="text-2xl font-bold tracking-tight sm:text-3xl lg:text-4xl">
              <span className="bg-gradient-to-br from-foreground via-foreground to-foreground/70 bg-clip-text text-transparent">
                Search & Discover
              </span>
              {" "}
              <span className="bg-gradient-to-r from-purple-500 via-pink-500 to-purple-500 bg-clip-text text-transparent">
                Your Documents
              </span>
            </h1>
            
            <p className="mx-auto max-w-2xl text-xs leading-relaxed text-muted-foreground sm:text-sm">
              Ask questions in natural language and find the most relevant matches.
            </p>
            
            {!isReady && (
              <Badge variant="destructive" className="gap-2 text-xs">
                <AlertCircle className="h-3 w-3" />
                System not ready
              </Badge>
            )}
          </div>

          {/* Search Form */}
          <form onSubmit={handleSearch} className="shrink-0 space-y-3">
            {/* Search Input with Buttons */}
            <div className="group relative overflow-hidden rounded-2xl border-2 border-border/50 bg-card/30 backdrop-blur-sm transition-all focus-within:border-primary/50 focus-within:shadow-xl focus-within:shadow-primary/10">
              <div className="absolute inset-0 bg-gradient-to-br from-purple-500 to-pink-500 opacity-0 transition-opacity group-focus-within:opacity-5" />
              
              <div className="relative flex items-center gap-3 p-3">
                <Search className="h-5 w-5 shrink-0 text-muted-foreground group-focus-within:text-primary transition-colors" />
                <input
                  type="text"
                  value={query}
                  onChange={(event) => setQuery(event.target.value)}
                  placeholder="Ask about content, visuals, or document details..."
                  className="flex-1 bg-transparent text-base outline-none placeholder:text-muted-foreground"
                  disabled={!isReady}
                />
                
                {/* Inline Button Group */}
                <div className="flex shrink-0 items-center gap-2">
                  <Button
                    type="submit"
                    size="sm"
                    disabled={loading || !isReady || !query.trim()}
                    className="group h-9 gap-2 rounded-full px-4 shadow-lg shadow-primary/20 transition-all hover:shadow-xl hover:shadow-primary/25"
                  >
                    {loading ? (
                      <>
                        <Loader2 className="h-4 w-4 animate-spin" />
                        <span className="hidden sm:inline">Searching...</span>
                      </>
                    ) : (
                      <>
                        <Search className="h-4 w-4" />
                        <span className="hidden sm:inline">Search</span>
                      </>
                    )}
                  </Button>
                  
                  <Button
                    type="button"
                    onClick={clearResults}
                    size="sm"
                    variant="ghost"
                    disabled={!hasSearched && !query}
                    className="h-9 gap-2 rounded-full px-3"
                  >
                    <X className="h-4 w-4" />
                    <span className="hidden sm:inline">Clear</span>
                  </Button>
                </div>
              </div>
            </div>

            {/* Settings Grid */}
            <div className="grid gap-3 sm:grid-cols-2">
              <div className="rounded-xl border border-border/50 bg-card/50 p-3 backdrop-blur-sm">
                <label className="flex flex-col gap-2">
                  <span className="text-xs font-medium text-muted-foreground">Neighbors (k)</span>
                  <input
                    type="number"
                    min={1}
                    value={k}
                    onChange={(event) => handleNumberChange(event, setK)}
                    className="rounded-lg border border-border/50 bg-background px-3 py-2 text-sm outline-none transition-all focus:border-primary/50 focus:ring-2 focus:ring-primary/20"
                  />
                </label>
              </div>
              <div className="rounded-xl border border-border/50 bg-card/50 p-3 backdrop-blur-sm">
                <label className="flex flex-col gap-2">
                  <span className="text-xs font-medium text-muted-foreground">Show top results</span>
                  <input
                    type="number"
                    min={1}
                    value={topK}
                    onChange={(event) => handleNumberChange(event, setTopK)}
                    className="rounded-lg border border-border/50 bg-background px-3 py-2 text-sm outline-none transition-all focus:border-primary/50 focus:ring-2 focus:ring-primary/20"
                  />
                </label>
              </div>
            </div>

            {/* Error Message */}
            {error && (
              <div className="flex items-center gap-2 rounded-lg bg-red-500/10 px-4 py-3 text-sm font-medium text-red-600 dark:text-red-400">
                <AlertCircle className="h-4 w-4" />
                {error}
              </div>
            )}

            {/* Suggested Queries */}
            {suggestedQueries.length > 0 && (
              <div className="space-y-2">
                <p className="text-xs font-medium text-muted-foreground">Quick suggestions:</p>
                <div className="flex flex-wrap gap-2">
                  {suggestedQueries.map((item) => (
                    <Button
                      key={item}
                      type="button"
                      onClick={() => setQuery(item)}
                      variant="outline"
                      size="sm"
                      className="h-auto rounded-full px-3 py-1.5 text-xs"
                    >
                      {item}
                    </Button>
                  ))}
                </div>
              </div>
            )}
          </form>

          {/* Results Section */}
          {(hasSearched || loading) && (
            <div className="flex min-h-0 flex-1 flex-col space-y-4">
              {/* Results Header */}
              <div className="flex flex-wrap items-center justify-center gap-3">
                <Badge variant="outline" className="gap-2 px-3 py-1">
                  <Sparkles className="h-3 w-3 text-primary" />
                  <span className="font-semibold">
                    {loading ? "Searching..." : `${truncatedResults.length} Results`}
                  </span>
                </Badge>
                
                {hasSearched && searchDurationMs !== null && (
                  <Badge variant="outline" className="gap-2 px-3 py-1">
                    <Clock className="h-3 w-3" />
                    {(searchDurationMs / 1000).toFixed(2)}s
                  </Badge>
                )}
                
                {hasSearched && results.length > topK && (
                  <Badge variant="secondary" className="px-3 py-1 text-xs">
                    Showing {truncatedResults.length} of {results.length}
                  </Badge>
                )}
              </div>

              {/* Loading State */}
              {loading && (
                <div className="flex items-center justify-center gap-2 rounded-xl border border-border/50 bg-card/50 p-8 backdrop-blur-sm">
                  <Loader2 className="h-5 w-5 animate-spin text-primary" />
                  <p className="text-sm text-muted-foreground">Searching your documents...</p>
                </div>
              )}

              {/* No Results */}
              {!loading && hasSearched && truncatedResults.length === 0 && (
                <div className="rounded-xl border border-border/50 bg-card/50 p-8 text-center backdrop-blur-sm">
                  <AlertCircle className="mx-auto h-12 w-12 text-muted-foreground/50" />
                  <p className="mt-3 text-sm font-medium text-foreground">No matches found</p>
                  <p className="mt-1 text-xs text-muted-foreground">
                    Try adjusting your query or search parameters
                  </p>
                </div>
              )}

              {/* Results List */}
              {!loading && truncatedResults.length > 0 && (
                <div className="min-h-0 flex-1 space-y-2 overflow-y-auto rounded-xl border border-border/50 bg-card/30 p-3 backdrop-blur-sm">
                  {truncatedResults.map((item, index) => (
                    <article 
                      key={`${item.label ?? index}-${index}`} 
                      className="group relative flex gap-3 overflow-hidden rounded-xl border border-border/50 bg-card/50 p-3 backdrop-blur-sm transition-all hover:border-primary/50 hover:shadow-lg hover:shadow-primary/10"
                    >
                      <div className="absolute inset-0 bg-gradient-to-br from-purple-500 to-pink-500 opacity-0 transition-opacity group-hover:opacity-5" />
                      
                      {/* Thumbnail */}
                      {item.image_url ? (
                        <div className="relative h-20 w-20 shrink-0 overflow-hidden rounded-lg border border-border/50 bg-background/50">
                          <Image
                            src={item.image_url}
                            alt={item.label ?? `Result ${index + 1}`}
                            width={80}
                            height={80}
                            className="h-full w-full object-cover"
                            unoptimized
                          />
                        </div>
                      ) : (
                        <div className="flex h-20 w-20 shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-purple-500 to-pink-500">
                          <FileText className="h-7 w-7 text-primary-foreground" />
                        </div>
                      )}
                      
                      {/* Content */}
                      <div className="relative flex min-w-0 flex-1 flex-col justify-between">
                        {/* Header */}
                        <div className="space-y-1">
                          <h3 className="line-clamp-2 text-sm font-bold text-foreground">
                            {item.label ?? `Result ${index + 1}`}
                          </h3>
                          <div className="flex flex-wrap gap-1.5">
                            {typeof item.score === "number" && (
                              <Badge variant="secondary" className="h-auto px-2 py-0.5 text-xs">
                                {Math.round(item.score * 100)}%
                              </Badge>
                            )}
                            {item.payload?.filename && (
                              <Badge variant="outline" className="h-auto max-w-[200px] truncate px-2 py-0.5 text-xs font-normal">
                                {item.payload.filename}
                              </Badge>
                            )}
                            {typeof item.payload?.pdf_page_index === "number" && (
                              <Badge variant="outline" className="h-auto px-2 py-0.5 text-xs font-normal">
                                Page {item.payload.pdf_page_index + 1}
                              </Badge>
                            )}
                          </div>
                        </div>
                      </div>
                    </article>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
