"use client";

import { useState, useEffect } from "react";
import type { SearchItem } from "@/lib/api/generated";
import { RetrievalService, ApiError } from "@/lib/api/generated";
import "@/lib/api/client";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { Separator } from "@/components/ui/separator";
import { Search, Loader2, AlertCircle, ImageIcon, Hash, Lightbulb, Clock, Sparkles, Eye } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { toast } from "sonner";
import Image from "next/image";
import ImageLightbox from "@/components/lightbox";

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
  const [q, setQ] = useState("");
  const [k, setK] = useState<number>(5);
  const [results, setResults] = useState<SearchItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasSearched, setHasSearched] = useState(false);
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
      const data = await RetrievalService.searchSearchGet(query, k);
      setResults(data);
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
      className="space-y-8"
    >
      {/* Header */}
      <div className="space-y-4">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-gradient-to-br from-blue-500/10 to-cyan-500/10 rounded-lg border border-blue-500/20">
            <Eye className="w-6 h-6 text-blue-500" />
          </div>
          <div>
            <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-cyan-600 bg-clip-text text-transparent">Visual Search</h1>
            <p className="text-muted-foreground text-lg">Find documents and images using natural language powered by AI vision</p>
          </div>
        </div>
        
        {/* Quick Stats */}
        <div className="flex items-center gap-6 text-sm text-muted-foreground">
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-blue-500" />
            <span>AI-powered visual understanding</span>
          </div>
          <div className="flex items-center gap-2">
            <Search className="w-4 h-4 text-cyan-500" />
            <span>Natural language queries</span>
          </div>
        </div>
      </div>

      {/* Search Form */}
      <Card className="border-2 border-blue-100/50 shadow-lg">
        <CardHeader className="bg-gradient-to-r from-blue-50/50 to-cyan-50/50 border-b">
          <CardTitle className="flex items-center gap-2 text-xl">
            <Search className="w-5 h-5 text-blue-600" />
            Search Your Documents
          </CardTitle>
          <CardDescription className="text-base">
            Describe what you're looking for using natural language. Our AI will find relevant visual content.
          </CardDescription>
        </CardHeader>
        <CardContent className="pt-6 space-y-6">
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
                    className="text-base pl-11 h-12 border-2 focus:border-blue-400 bg-white"
                  />
                </div>
                <div className="flex items-center gap-2">
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <div className="flex items-center gap-1">
                        <Hash className="w-4 h-4 text-muted-foreground" />
                        <Select value={k.toString()} onValueChange={(value) => setK(parseInt(value, 10))} disabled={loading}>
                          <SelectTrigger className="w-20 h-12">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            {[1, 3, 5, 10, 15, 20].map((num) => (
                              <SelectItem key={num} value={num.toString()}>{num}</SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                    </TooltipTrigger>
                    <TooltipContent>
                      <p>Number of results to show</p>
                    </TooltipContent>
                  </Tooltip>
                  <Button 
                    type="submit" 
                    disabled={loading || !q.trim()} 
                    size="lg" 
                    className="h-12 px-6 bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-700 hover:to-cyan-700"
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
          
          {/* Example Queries */}
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <Lightbulb className="w-4 h-4 text-yellow-500" />
              <span className="text-sm font-medium text-muted-foreground">Try these examples:</span>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
              {exampleQueries.map((example, idx) => (
                <motion.button
                  key={idx}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={() => handleExampleClick(example.text)}
                  disabled={loading}
                  className="text-left p-3 rounded-lg border border-muted-foreground/20 hover:border-blue-300 hover:bg-blue-50/30 transition-all group disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <div className="text-sm font-medium text-foreground group-hover:text-blue-700 transition-colors">
                    "{example.text}"
                  </div>
                  <Badge variant="outline" className="text-xs mt-1">{example.category}</Badge>
                </motion.button>
              ))}
            </div>
          </div>
          
          {/* Recent Searches */}
          <AnimatePresence>
            {recentSearches.length > 0 && !hasSearched && (
              <motion.div 
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                exit={{ opacity: 0, height: 0 }}
                className="space-y-3"
              >
                <div className="flex items-center gap-2">
                  <Clock className="w-4 h-4 text-muted-foreground" />
                  <span className="text-sm font-medium text-muted-foreground">Recent searches:</span>
                </div>
                <div className="flex flex-wrap gap-2">
                  {recentSearches.map((search, idx) => (
                    <motion.button
                      key={idx}
                      whileHover={{ scale: 1.05 }}
                      onClick={() => setQ(search)}
                      disabled={loading}
                      className="px-3 py-1 text-sm bg-muted/50 hover:bg-blue-100 rounded-full transition-colors disabled:opacity-50"
                    >
                      {search}
                    </motion.button>
                  ))}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </CardContent>
      </Card>

      {/* Error State */}
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

      {/* Results */}
      <AnimatePresence>
        {hasSearched && !loading && !error && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="space-y-4"
          >
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div className="space-y-1">
                <h2 className="text-2xl font-bold">
                  {results.length > 0 ? `Found ${results.length} result${results.length !== 1 ? 's' : ''}` : "No results found"}
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
              <motion.div 
                variants={containerVariants}
                initial="hidden"
                animate="visible"
                className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6"
              >
                {results.map((item, idx) => (
                  <motion.div key={idx} variants={itemVariants}>
                    <Card className="h-full group overflow-hidden hover:shadow-xl transition-all duration-300 hover:-translate-y-2 border-2 hover:border-blue-200">
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
                            <Badge className="bg-white/90 text-black">
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
                        <div className="flex items-center justify-between pt-2 border-t border-muted/30">
                          <div className="flex items-center gap-2">
                            <Badge variant="outline" className="text-xs font-medium">
                              #{idx + 1}
                            </Badge>
                            {typeof item.score === "number" && (
                              <div className="flex items-center gap-1">
                                <div className={`w-2 h-2 rounded-full ${
                                  item.score > 0.8 ? 'bg-green-500' : item.score > 0.6 ? 'bg-yellow-500' : 'bg-red-500'
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
