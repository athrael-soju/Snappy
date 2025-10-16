"use client";

import { ChangeEvent, FormEvent, useMemo, useState } from "react";
import "@/lib/api/client";
import Image from "next/image";
import { RetrievalService } from "@/lib/api/generated";
import { parseSearchResults } from "@/lib/api/runtime";
import { useSearchStore } from "@/lib/hooks/use-search-store";
import { useSystemStatus } from "@/stores/app-store";
import { Page, PageSection } from "@/components/layout/page";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";

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

  const canClear = hasSearched || Boolean(query.trim());
  const showEmptyState = !loading && hasSearched && truncatedResults.length === 0;
  const resultCountSummary =
    hasSearched && truncatedResults.length > 0 ? `Showing ${truncatedResults.length} of ${results.length} matches` : undefined;

  return (
    <Page
      title="Search"
      description="Submit a text query and review the most relevant matches from the indexed documents."
      actions={
        <Button variant="outline" size="sm" onClick={clearResults} disabled={!canClear}>
          Clear
        </Button>
      }
    >
      <PageSection>
        <Card>
          <CardHeader className="gap-3">
            <CardTitle>Query parameters</CardTitle>
            <CardDescription>Adjust retrieval settings and launch your search.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-(--space-section-stack)">
            {!isReady && (
              <Alert variant="destructive">
                <AlertTitle>Search backend unavailable</AlertTitle>
                <AlertDescription>Initialize the system before running queries.</AlertDescription>
              </Alert>
            )}

            {error && (
              <Alert variant="destructive">
                <AlertTitle>Search failed</AlertTitle>
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            <form
              onSubmit={handleSearch}
              className="flex flex-col gap-(--space-section-stack)"
            >
              <div className="flex flex-col gap-2">
                <Label htmlFor="query">Query</Label>
                <Input
                  id="query"
                  value={query}
                  onChange={(event) => setQuery(event.target.value)}
                  placeholder="Ask about filenames, content, or visual details"
                  disabled={!isReady}
                />
              </div>

              <div className="grid gap-(--space-section-stack) sm:grid-cols-2">
                <div className="flex flex-col gap-2">
                  <Label htmlFor="neighbors">Neighbors (k)</Label>
                  <Input
                    id="neighbors"
                    type="number"
                    min={1}
                    value={k}
                    onChange={(event) => handleNumberChange(event, setK)}
                  />
                </div>
                <div className="flex flex-col gap-2">
                  <Label htmlFor="top-results">Show top results</Label>
                  <Input
                    id="top-results"
                    type="number"
                    min={1}
                    value={topK}
                    onChange={(event) => handleNumberChange(event, setTopK)}
                  />
                </div>
              </div>

              <div className="flex flex-wrap items-center gap-3">
                <Button
                  type="submit"
                  disabled={loading || !isReady || !query.trim()}
                >
                  {loading ? "Searching..." : "Search"}
                </Button>
                {loading && (
                  <Badge variant="secondary">Running search</Badge>
                )}
              </div>

              {suggestedQueries.length > 0 && (
                <div className="flex flex-col gap-2">
                  <span className="text-sm font-medium text-foreground">Try one of these</span>
                  <div className="flex flex-wrap gap-2">
                    {suggestedQueries.map((item) => (
                      <Button
                        key={item}
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={() => setQuery(item)}
                      >
                        {item}
                      </Button>
                    ))}
                  </div>
                </div>
              )}
            </form>
          </CardContent>
        </Card>
      </PageSection>

      <PageSection>
        <Card>
          <CardHeader className="gap-3">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div className="flex flex-col gap-1">
                <CardTitle>Results</CardTitle>
                <CardDescription>
                  Review the retrieved items after each query.
                </CardDescription>
              </div>
              <div className="flex flex-wrap items-center gap-2 text-xs">
                {hasSearched && searchDurationMs !== null && (
                  <Badge variant="secondary">
                    {(searchDurationMs / 1000).toFixed(2)}s
                  </Badge>
                )}
                {resultCountSummary && <Badge variant="outline">{resultCountSummary}</Badge>}
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-(--space-section-stack)">
            {showEmptyState && (
              <Alert>
                <AlertTitle>No matches</AlertTitle>
                <AlertDescription>
                  No results found for “{query}”. Try adjusting your query terms or retrieval settings.
                </AlertDescription>
              </Alert>
            )}

            {!showEmptyState && (
              <div className="flex flex-col divide-y divide-border">
                {truncatedResults.map((item, index) => (
                  <article
                    key={`${item.label ?? index}-${index}`}
                    className="space-y-3 py-6 first:pt-0 last:pb-0"
                  >
                    <header className="flex flex-col gap-1">
                      <h3 className="text-base font-semibold text-foreground">
                        {item.label ?? `Result ${index + 1}`}
                      </h3>
                      <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                        {typeof item.score === "number" && (
                          <Badge variant="outline">
                            Score {Math.round(item.score * 100)}%
                          </Badge>
                        )}
                      </div>
                    </header>

                    {item.image_url && (
                      <div className="overflow-hidden rounded-lg border border-border">
                        <Image
                          src={item.image_url}
                          alt={item.label ?? `Result image ${index + 1}`}
                          width={512}
                          height={512}
                          className="h-auto w-full object-contain"
                          unoptimized
                        />
                      </div>
                    )}

                    <dl className="grid gap-1 text-sm text-muted-foreground">
                      {item.payload?.filename && (
                        <div className="flex flex-wrap gap-2">
                          <dt className="font-medium text-foreground">File</dt>
                          <dd>{item.payload.filename}</dd>
                        </div>
                      )}
                      {typeof item.payload?.pdf_page_index === "number" && (
                        <div className="flex flex-wrap gap-2">
                          <dt className="font-medium text-foreground">Page</dt>
                          <dd>{item.payload.pdf_page_index + 1}</dd>
                        </div>
                      )}
                      {Object.entries(item.payload ?? {})
                        .filter(([key]) => key !== "filename" && key !== "pdf_page_index")
                        .map(([key, value]) => (
                          <div key={key} className="flex flex-wrap gap-2">
                            <dt className="font-medium text-foreground">{key}</dt>
                            <dd>{String(value)}</dd>
                          </div>
                        ))}
                    </dl>
                  </article>
                ))}

                {!hasSearched && (
                  <div className="py-6 text-sm text-muted-foreground">
                    Run a search to see matching results here.
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      </PageSection>
    </Page>
  );
}
