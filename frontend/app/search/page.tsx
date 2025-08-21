"use client";

import { useState } from "react";
import type { SearchItem } from "@/lib/api/generated";
import { RetrievalService, ApiError } from "@/lib/api/generated";
import "@/lib/api/client";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import Image from "next/image";

export default function SearchPage() {
  const [q, setQ] = useState("");
  const [k, setK] = useState<number>(5);
  const [results, setResults] = useState<SearchItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const data = await RetrievalService.searchSearchGet(q, k);
      setResults(data);
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        setError(`${err.status}: ${err.message}`);
      } else {
        setError("Search failed");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold">Search</h1>
      <form onSubmit={onSubmit} className="flex flex-col sm:flex-row gap-3 items-start">
        <Input
          placeholder="Enter your query..."
          value={q}
          onChange={(e) => setQ(e.target.value)}
          required
          className="w-full sm:w-96"
        />
        <Input
          type="number"
          min={1}
          max={50}
          value={k}
          onChange={(e) => setK(parseInt(e.target.value || "5", 10))}
          title="Top K"
          className="w-24"
        />
        <Button type="submit" disabled={loading}>
          {loading ? (
            <span className="inline-flex items-center gap-2"><Spinner size={16} /> Searching...</span>
          ) : (
            "Search"
          )}
        </Button>
      </form>

      {error && (
        <div className="text-red-600 text-sm" role="alert">{error}</div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
        {results.map((item, idx) => (
          <Card key={idx}>
            <CardContent className="p-3 space-y-2">
              {item.image_url && (
                <Image
                  src={item.image_url}
                  alt={item.label ?? `Result ${idx + 1}`}
                  width={1200}
                  height={800}
                  sizes="(max-width: 640px) 100vw, (max-width: 768px) 50vw, 33vw"
                  className="w-full h-auto rounded"
                />
              )}
              {item.label && (
                <div className="text-sm font-medium">{item.label}</div>
              )}
              {typeof item.score === "number" && (
                <div className="text-xs text-black/60 dark:text-white/60">Score: {item.score.toFixed(3)}</div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
