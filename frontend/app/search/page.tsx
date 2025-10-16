"use client";

import { ChangeEvent, FormEvent, useMemo, useState } from "react";
import "@/lib/api/client";
import Image from "next/image";
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
    <main className="mx-auto flex max-w-5xl flex-col gap-6 p-4">
      <header className="space-y-2">
        <h1 className="text-2xl font-semibold text-foreground">Search</h1>
        <p className="text-sm text-muted-foreground">
          Submit a text query and view the most relevant matches from the indexed documents. This simplified page keeps the form and results list only.
        </p>
        {!isReady && (
          <p className="text-sm text-red-600 dark:text-red-400">
            The search backend is not ready yet. Initialize the system first.
          </p>
        )}
      </header>

      <section className="space-y-4 rounded border border-border p-4">
        <form onSubmit={handleSearch} className="space-y-3 text-sm">
          <label className="flex flex-col gap-1">
            <span className="font-medium text-foreground">Query</span>
            <input
              type="text"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Ask about filenames, content, or visual details"
              className="rounded border border-border px-3 py-2"
              disabled={!isReady}
            />
          </label>

          <div className="grid gap-3 sm:grid-cols-2">
            <label className="flex flex-col gap-1">
              <span className="font-medium text-foreground">Neighbors (k)</span>
              <input
                type="number"
                min={1}
                value={k}
                onChange={(event) => handleNumberChange(event, setK)}
                className="rounded border border-border px-3 py-2"
              />
            </label>
            <label className="flex flex-col gap-1">
              <span className="font-medium text-foreground">Show top results</span>
              <input
                type="number"
                min={1}
                value={topK}
                onChange={(event) => handleNumberChange(event, setTopK)}
                className="rounded border border-border px-3 py-2"
              />
            </label>
          </div>

          <div className="flex flex-wrap gap-3">
            <button
              type="submit"
              className="rounded bg-primary px-4 py-2 font-medium text-primary-foreground disabled:opacity-50"
              disabled={loading || !isReady || !query.trim()}
            >
              {loading ? "Searching..." : "Search"}
            </button>
            <button
              type="button"
              onClick={clearResults}
              className="rounded border border-border px-4 py-2 font-medium text-foreground disabled:opacity-50"
              disabled={!hasSearched && !query}
            >
              Clear
            </button>
          </div>

          {error && <p className="text-sm text-red-600 dark:text-red-400">{error}</p>}
          {suggestedQueries.length > 0 && (
            <div className="space-y-1 text-xs text-muted-foreground">
              <p className="font-medium text-foreground">Try one of these:</p>
              <ul className="flex flex-wrap gap-2">
                {suggestedQueries.map((item) => (
                  <li key={item}>
                    <button
                      type="button"
                      onClick={() => setQuery(item)}
                      className="rounded border border-border px-2 py-1"
                    >
                      {item}
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </form>
      </section>

      <section className="space-y-3 rounded border border-border p-4 text-sm">
        <header className="flex flex-wrap items-center gap-3">
          <h2 className="text-base font-semibold text-foreground">Results</h2>
          {hasSearched && searchDurationMs !== null && (
            <span className="text-xs text-muted-foreground">
              Retrieved in {(searchDurationMs / 1000).toFixed(2)}s
            </span>
          )}
          {hasSearched && (
            <span className="text-xs text-muted-foreground">
              Showing {truncatedResults.length} of {results.length} matches
            </span>
          )}
        </header>

        {loading && <p className="text-xs text-muted-foreground">Running search...</p>}

        {!loading && hasSearched && truncatedResults.length === 0 && (
          <p className="text-xs text-muted-foreground">
            No matches found for &quot;{query}&quot;.
          </p>
        )}

        <div className="space-y-3">
          {truncatedResults.map((item, index) => (
            <article key={`${item.label ?? index}-${index}`} className="space-y-2 rounded border border-dashed border-border p-3">
              <header className="space-y-1">
                <h3 className="text-sm font-semibold text-foreground">{item.label ?? `Result ${index + 1}`}</h3>
                {typeof item.score === "number" && (
                  <p className="text-xs text-muted-foreground">Score: {Math.round(item.score * 100)}%</p>
                )}
              </header>

              {item.image_url && (
                <div className="flex justify-center">
                  <Image
                    src={item.image_url}
                    alt={item.label ?? `Result image ${index + 1}`}
                    width={512}
                    height={512}
                    className="max-h-64 w-auto rounded border border-border object-contain"
                    unoptimized
                  />
                </div>
              )}

              <ul className="space-y-1 text-xs text-muted-foreground">
                {item.payload?.filename && <li>File: {item.payload.filename}</li>}
                {typeof item.payload?.pdf_page_index === "number" && (
                  <li>Page: {item.payload.pdf_page_index + 1}</li>
                )}
                {Object.entries(item.payload ?? {})
                  .filter(([key]) => key !== "filename" && key !== "pdf_page_index")
                  .map(([key, value]) => (
                    <li key={key}>
                      {key}: {String(value)}
                    </li>
                  ))}
              </ul>
            </article>
          ))}
        </div>
      </section>
    </main>
  );
}
