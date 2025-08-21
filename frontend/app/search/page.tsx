"use client";

import { useState } from "react";
import type { SearchItem } from "@/lib/api/generated";
import { RetrievalService, ApiError } from "@/lib/api/generated";
import "@/lib/api/client";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Search, Loader2, AlertCircle, ImageIcon, Hash } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { toast } from "sonner";
import Image from "next/image";

export default function SearchPage() {
  const [q, setQ] = useState("");
  const [k, setK] = useState<number>(5);
  const [results, setResults] = useState<SearchItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasSearched, setHasSearched] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!q.trim()) return;
    
    setLoading(true);
    setError(null);
    setHasSearched(true);
    
    try {
      const data = await RetrievalService.searchSearchGet(q.trim(), k);
      setResults(data);
      toast.success(`Found ${data.length} results`);
    } catch (err: unknown) {
      let errorMsg = "Search failed";
      if (err instanceof ApiError) {
        errorMsg = `${err.status}: ${err.message}`;
      } else if (err instanceof Error) {
        errorMsg = err.message;
      }
      setError(errorMsg);
      toast.error("Search Failed", { description: errorMsg });
    } finally {
      setLoading(false);
    }
  }

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1
      }
    }
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: {
      opacity: 1,
      y: 0,
      transition: { duration: 0.3 }
    }
  };

  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="space-y-8"
    >
      {/* Header */}
      <div className="space-y-2">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-blue-500/10 rounded-lg">
            <Search className="w-6 h-6 text-blue-500" />
          </div>
          <div>
            <h1 className="text-3xl font-bold">Visual Search</h1>
            <p className="text-muted-foreground">Find documents and images using natural language</p>
          </div>
        </div>
      </div>

      {/* Search Form */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Search className="w-5 h-5" />
            Search Query
          </CardTitle>
          <CardDescription>
            Enter your search terms to find relevant visual content
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={onSubmit} className="space-y-4">
            <div className="flex flex-col sm:flex-row gap-3">
              <div className="flex-1">
                <Input
                  placeholder="Describe what you're looking for..."
                  value={q}
                  onChange={(e) => setQ(e.target.value)}
                  required
                  disabled={loading}
                  className="text-base"
                />
              </div>
              <div className="flex items-center gap-2">
                <div className="flex items-center gap-1">
                  <Hash className="w-4 h-4 text-muted-foreground" />
                  <Input
                    type="number"
                    min={1}
                    max={20}
                    value={k}
                    onChange={(e) => setK(parseInt(e.target.value || "5", 10))}
                    title="Number of results"
                    className="w-20 text-center"
                    disabled={loading}
                  />
                </div>
                <Button type="submit" disabled={loading || !q.trim()} size="lg">
                  {loading ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Searching...
                    </>
                  ) : (
                    <>
                      <Search className="w-4 h-4 mr-2" />
                      Search
                    </>
                  )}
                </Button>
              </div>
            </div>
          </form>
        </CardContent>
      </Card>

      {/* Error State */}
      <AnimatePresence>
        {error && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className="flex items-center gap-2 p-4 bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-800 rounded-lg text-red-800 dark:text-red-200"
            role="alert"
          >
            <AlertCircle className="w-5 h-5" />
            <span className="font-medium">{error}</span>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Results */}
      <AnimatePresence>
        {hasSearched && !loading && !error && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="space-y-4"
          >
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-semibold">
                {results.length > 0 ? `Found ${results.length} results` : "No results found"}
              </h2>
              {results.length > 0 && (
                <Badge variant="secondary" className="text-sm">
                  Query: "{q}"
                </Badge>
              )}
            </div>

            {results.length === 0 ? (
              <Card>
                <CardContent className="flex flex-col items-center justify-center py-12 text-center">
                  <div className="w-16 h-16 bg-muted rounded-full flex items-center justify-center mb-4">
                    <ImageIcon className="w-8 h-8 text-muted-foreground" />
                  </div>
                  <h3 className="text-lg font-medium mb-2">No results found</h3>
                  <p className="text-muted-foreground max-w-md">
                    Try adjusting your search terms or upload more documents to search through.
                  </p>
                </CardContent>
              </Card>
            ) : (
              <motion.div 
                variants={containerVariants}
                initial="hidden"
                animate="visible"
                className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6"
              >
                {results.map((item, idx) => (
                  <motion.div key={idx} variants={itemVariants}>
                    <Card key={idx} className="h-full group overflow-hidden hover:shadow-md transition-all duration-300 hover:-translate-y-1">
                      {item.image_url && (
                        <div className="relative aspect-video overflow-hidden bg-muted">
                          <Image
                            src={item.image_url}
                            alt={item.label ?? `Result ${idx + 1}`}
                            fill
                            sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 33vw"
                            className="object-cover group-hover:scale-105 transition-transform duration-300"
                          />
                          <div className="absolute inset-0 bg-gradient-to-t from-black/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                        </div>
                      )}
                      <CardContent className="p-4 space-y-3">
                        {item.label && (
                          <h3 className="font-medium text-foreground line-clamp-2 group-hover:text-primary transition-colors">
                            {item.label}
                          </h3>
                        )}
                        <div className="flex items-center justify-between">
                          <Badge variant="outline" className="text-xs">
                            #{idx + 1}
                          </Badge>
                          {typeof item.score === "number" && (
                            <Badge variant="secondary" className="text-xs">
                              Score: {item.score.toFixed(3)}
                            </Badge>
                          )}
                        </div>
                      </CardContent>
                    </Card>
                  </motion.div>
                ))}
              </motion.div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
