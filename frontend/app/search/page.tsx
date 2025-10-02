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
      className="space-y-4 min-h-0 flex flex-col flex-1 overflow-y-auto custom-scrollbar"
    >
      {/* Header with Background Decoration */}
      <div className="space-y-3 text-center relative">
        {/* Background decoration */}
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute top-0 left-20 w-32 h-32 bg-blue-200/20 rounded-full blur-xl" />
          <div className="absolute top-10 right-32 w-24 h-24 bg-cyan-200/20 rounded-full blur-xl" />
        </div>
        
        <h1 className="text-3xl sm:text-4xl font-bold bg-gradient-to-r from-blue-600 via-cyan-600 to-blue-600 bg-clip-text text-transparent relative z-10">
          Visual Search
        </h1>
        <p className="text-muted-foreground text-sm sm:text-base max-w-2xl mx-auto relative z-10">
          Find documents and images using natural language powered by AI vision
        </p>

        {/* Quick Stats */}
        <div className="flex flex-wrap justify-center items-center gap-3 sm:gap-4 text-xs text-muted-foreground relative z-10">
          <div className="flex items-center gap-1.5">
            <Sparkles className="w-3.5 h-3.5 text-blue-500" />
            <span>AI-powered visual understanding</span>
          </div>
          <div className="flex items-center gap-1.5">
            <Search className="w-3.5 h-3.5 text-cyan-500" />
            <span>Natural language queries</span>
          </div>
        </div>
      </div>

      {/* Search Form */}
      <Card className="border-2 border-blue-200/50 shadow-lg bg-gradient-to-br from-blue-500/5 to-cyan-500/5 hover:shadow-xl transition-shadow duration-300">
        <CardHeader className="bg-gradient-to-r from-blue-100/50 via-cyan-100/50 to-blue-100/50 border-b border-blue-200/50 py-4">
          <div className="flex items-center gap-2.5">
            <div className="p-1.5 rounded-xl bg-white border-2 border-blue-200/50 shadow-sm">
              <Search className="w-4 h-4 text-blue-500" />
            </div>
            <div>
              <CardTitle className="text-lg font-bold">Search Your Documents</CardTitle>
              <CardDescription className="text-sm mt-0.5">
                Describe what you're looking for using natural language.
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="pt-5 pb-5 space-y-5">
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

      {/* Pre-search Placeholder / Results */
      }
      {!hasSearched && !loading && !error && (
        <Card className="border-2 border-dashed border-muted-foreground/25">
          <CardContent className="flex flex-col items-center justify-center py-16 text-center">
            <div className="w-20 h-20 bg-gradient-to-br from-muted/50 to-muted/30 rounded-full flex items-center justify-center mb-6">
              <Search className="w-10 h-10 text-muted-foreground" />
            </div>
            <h3 className="text-xl font-semibold mb-2">Your results will appear here</h3>
            <p className="text-muted-foreground max-w-md">
              Use natural language to find documents and images instantly.
            </p>
          </CardContent>
        </Card>
      )}

      {/* Results */
      }
      <AnimatePresence>
        {hasSearched && !loading && !error && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="space-y-4 flex-shrink-0"
          >
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div className="space-y-1">
                <h2 className="text-2xl font-bold">
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
                  <p className="text-muted-foreground">
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
                  <h3 className="text-xl font-semibold mb-3">No matches found</h3>
                  <p className="text-muted-foreground max-w-md mb-6">
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
              <div className="flex-1 min-h-0 overflow-y-auto custom-scrollbar">
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
                            <h3 className="font-semibold text-foreground line-clamp-2 group-hover:text-blue-600 transition-colors">
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
                              <div className="flex items-center gap-1">
                                <div className={`w-2 h-2 rounded-full ${item.score > 0.8 ? 'bg-green-500' : item.score > 0.6 ? 'bg-yellow-500' : 'bg-red-500'
                                  }`} />
                                <span className="text-xs text-muted-foreground font-mono">
                                  {(item.score * 100).toFixed(1)}%
                                </span>
                              </div>
                            )}
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  </motion.div>
                ))}
                </motion.div>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
      <ImageLightbox
        open={lightboxOpen}
        src={lightboxSrc}
        alt={lightboxAlt}
        onOpenChange={setLightboxOpen}
      />
    </motion.div>
  );
}
