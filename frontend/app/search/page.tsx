"use client";

import { useState, useEffect } from "react";
import type { SearchItem } from "@/lib/api/generated";
import { RetrievalService, ApiError } from "@/lib/api/generated";
import "@/lib/api/client";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Search, AlertCircle, ImageIcon, Sparkles, Eye, Trash2 } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { toast } from "@/components/ui/sonner";
import Image from "next/image";
import ImageLightbox from "@/components/lightbox";
import SearchBar from "@/components/search/SearchBar";
// import ExampleQueries from "@/components/search/ExampleQueries";
import RecentSearchesChips from "@/components/search/RecentSearchesChips";
import { useSearchStore } from "@/stores/app-store";
import { PageHeader } from "@/components/page-header";

// Example search prompts to help users
const exampleQueries = [
  { text: "Find invoices with company logo", category: "Documents" },
  { text: "Show slides about product launch", category: "Presentations" },
  { text: "Charts with financial data", category: "Analysis" },
  { text: "Images with people in meetings", category: "Photos" },
  { text: "Technical diagrams or flowcharts", category: "Technical" },
  { text: "Contract documents with signatures", category: "Legal" }
];

export default function SearchPage() {
  // Use global search store instead of local state
  const {
    query: q,
    results,
    hasSearched,
    searchDurationMs,
    k,
    setQuery: setQ,
    setResults,
    setHasSearched,
    setK,
    reset,
  } = useSearchStore();

  // Local state for UI interactions only
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lightboxOpen, setLightboxOpen] = useState(false);
  const [lightboxSrc, setLightboxSrc] = useState("");
  const [lightboxAlt, setLightboxAlt] = useState<string | undefined>(undefined);
  const [recentSearches, setRecentSearches] = useState<string[]>([]);

  // Load recent searches from localStorage
  useEffect(() => {
    const saved = localStorage.getItem('colpali-recent-searches');
    if (saved) {
      try {
        setRecentSearches(JSON.parse(saved));
      } catch {
        // Ignore parse errors
      }
    }
  }, []);

  const addToRecentSearches = (query: string) => {
    const updated = [query, ...recentSearches.filter(s => s !== query)].slice(0, 5);
    setRecentSearches(updated);
    localStorage.setItem('colpali-recent-searches', JSON.stringify(updated));
  };

  const removeFromRecentSearches = (query: string) => {
    const updated = recentSearches.filter(s => s !== query);
    setRecentSearches(updated);
    localStorage.setItem('colpali-recent-searches', JSON.stringify(updated));
  };

  const handleExampleClick = (example: string) => {
    setQ(example);
  };

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    const query = q.trim();
    if (!query) return;

    setLoading(true);
    setError(null);
    setHasSearched(true);

    // Add to recent searches
    addToRecentSearches(query);

    try {
      const start = performance.now();
      const data = await RetrievalService.searchSearchGet(query, k);
      const end = performance.now();
      setResults(data, end - start);
      toast.success(`Found ${data.length} results for "${query}"`);
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
      className="space-y-4 min-h-0 flex flex-col flex-1"
    >
      <PageHeader
        title="Visual Search"
        description="Find documents and images using natural language powered by AI vision"
        icon={Search}
      />

      {/* Search Form */}
      <Card className="border-2 border-blue-200/50 shadow-lg bg-gradient-to-br from-blue-500/5 to-cyan-500/5 hover:shadow-xl transition-shadow duration-300">
        <CardContent className="pt-6 pb-6 space-y-4">
          <SearchBar
            q={q}
            setQ={setQ}
            loading={loading}
            onSubmit={onSubmit}
            k={k}
            setK={setK}
            hasResults={hasSearched && results.length > 0}
            onClear={() => {
              reset();
              setError(null);
              toast.success('Search results cleared');
            }}
          />

          <RecentSearchesChips
            recentSearches={recentSearches}
            loading={loading}
            visible={!hasSearched}
            onSelect={(s) => setQ(s)}
            onRemove={removeFromRecentSearches}
          />
        </CardContent>
      </Card>

      {/* Error State */
      }
      <AnimatePresence>
        {error && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
          >
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Pre-search Placeholder / Results - Scrollable Container */}
      <div className="flex-1 min-h-0 overflow-y-auto custom-scrollbar">
        {!hasSearched && !loading && !error && (
          <Card className="border-2 border-dashed border-muted-foreground/25">
            <CardContent className="flex flex-col items-center justify-center py-16 text-center">
              <div className="w-20 h-20 bg-gradient-to-br from-muted/50 to-muted/30 rounded-full flex items-center justify-center mb-6">
                <Search className="w-10 h-10 text-muted-foreground" />
              </div>
              <h3 className="text-xl font-medium mb-2">Your results will appear here</h3>
              <p className="text-muted-foreground max-w-md leading-relaxed">
                Use natural language to find documents and images instantly.
              </p>
            </CardContent>
          </Card>
        )}

        {/* Results */}
        <AnimatePresence>
          {hasSearched && !loading && !error && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="space-y-4 pb-4"
            >
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div className="space-y-1">
                <h2 className="text-2xl font-semibold">
                  {results.length > 0 ? (
                    <>
                      {`Found ${results.length} result${results.length !== 1 ? 's' : ''}`}
                      {typeof searchDurationMs === 'number' && (
                        <span className="text-base font-normal text-muted-foreground ml-2">
                          in {(searchDurationMs / 1000).toFixed(2)}s
                        </span>
                      )}
                    </>
                  ) : (
                    ""
                  )}
                </h2>
                {results.length > 0 && (
                  <p className="text-sm text-muted-foreground">
                    Showing visual matches for your search
                  </p>
                )}
              </div>
              {results.length > 0 && (
                <div className="flex items-center gap-2">
                  <Badge variant="secondary" className="text-sm px-3 py-1">
                    "{q}"
                  </Badge>
                  <Badge variant="outline" className="text-xs">
                    {k} results
                  </Badge>
                </div>
              )}
            </div>

            {results.length === 0 ? (
              <Card className="border-2 border-dashed border-muted-foreground/25">
                <CardContent className="flex flex-col items-center justify-center py-16 text-center">
                  <div className="w-20 h-20 bg-gradient-to-br from-muted/50 to-muted/30 rounded-full flex items-center justify-center mb-6">
                    <ImageIcon className="w-10 h-10 text-muted-foreground" />
                  </div>
                  <h3 className="text-xl font-medium mb-3">No matches found</h3>
                  <p className="text-muted-foreground max-w-md mb-6 leading-relaxed">
                    We couldn't find any visual content matching "<span className="font-medium text-foreground">{q}</span>". Try rephrasing your query or check if documents are uploaded.
                  </p>
                  <div className="space-y-3">
                    <p className="text-sm font-medium text-muted-foreground">Suggestions:</p>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-sm">
                      <div className="flex items-start gap-2">
                        <div className="w-1.5 h-1.5 bg-blue-500 rounded-full mt-2 flex-shrink-0"></div>
                        <span className="text-muted-foreground">Try simpler, more descriptive terms</span>
                      </div>
                      <div className="flex items-start gap-2">
                        <div className="w-1.5 h-1.5 bg-blue-500 rounded-full mt-2 flex-shrink-0"></div>
                        <span className="text-muted-foreground">Check spelling and grammar</span>
                      </div>
                      <div className="flex items-start gap-2">
                        <div className="w-1.5 h-1.5 bg-blue-500 rounded-full mt-2 flex-shrink-0"></div>
                        <span className="text-muted-foreground">Upload more diverse content</span>
                      </div>
                      <div className="flex items-start gap-2">
                        <div className="w-1.5 h-1.5 bg-blue-500 rounded-full mt-2 flex-shrink-0"></div>
                        <span className="text-muted-foreground">Try the example queries above</span>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ) : (
              <motion.div
                variants={containerVariants}
                initial="hidden"
                animate="visible"
                className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 pb-6 px-1"
              >
              {results.map((item, idx) => (
                  <motion.div key={idx} variants={itemVariants}>
                    <Card className="h-full group overflow-hidden hover:shadow-2xl transition-all duration-300 hover:-translate-y-1 border-2 border-blue-200/50 hover:border-blue-300 bg-gradient-to-br from-blue-500/5 to-cyan-500/5">
                      {item.image_url && (
                        <div
                          className="relative aspect-video overflow-hidden bg-gradient-to-br from-blue-50 to-cyan-50 cursor-zoom-in"
                          onClick={() => {
                            setLightboxSrc(item.image_url!);
                            setLightboxAlt(item.label ?? `Result ${idx + 1}`);
                            setLightboxOpen(true);
                          }}
                        >
                          <Image
                            src={item.image_url}
                            alt={item.label ?? `Result ${idx + 1}`}
                            fill
                            sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 33vw"
                            className="object-cover group-hover:scale-110 transition-transform duration-500"
                          />
                          <div className="absolute inset-0 bg-gradient-to-t from-black/40 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                          <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity">
                            <Badge className="bg-white/90 text-black shadow-md">
                              <Eye className="w-3 h-3 mr-1" />
                              View
                            </Badge>
                          </div>
                        </div>
                      )}
                      <CardContent className="p-4 space-y-3">
                        {item.label && (
                          <div className="space-y-1">
                            <h3 className="text-base font-medium text-foreground line-clamp-2 group-hover:text-blue-600 transition-colors">
                              {item.label}
                            </h3>
                          </div>
                        )}
                        <div className="flex items-center justify-between pt-2 border-t border-blue-200/30">
                          <div className="flex items-center gap-2">
                            <Badge variant="outline" className="text-xs font-medium border-blue-200/50">
                              #{idx + 1}
                            </Badge>
                            {typeof item.score === "number" && (
                              <Badge variant="outline" className="text-xs font-medium border-blue-200/50">
                                Score {Math.round(item.score * 100)}
                              </Badge>
                            )}
                          </div>
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
      </div>
      <ImageLightbox
        open={lightboxOpen}
        src={lightboxSrc}
        alt={lightboxAlt}
        onOpenChange={setLightboxOpen}
      />
    </motion.div>
  );
}
