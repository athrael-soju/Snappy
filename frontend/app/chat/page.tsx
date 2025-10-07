"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { useChat } from "@/lib/hooks/use-chat";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
// Removed Select in favor of a clearer segmented control
import { Alert, AlertDescription } from "@/components/ui/alert";
import { User, Image as ImageIcon, Loader2, Sparkles, Brain, FileText, BarChart3, MessageSquare, Clock, ExternalLink } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { defaultPageMotion, fadeInPresence, sectionVariants } from "@/lib/motion-presets";
import { toast } from "@/components/ui/sonner";
import ImageLightbox from "@/components/lightbox";
import ChatInputBar from "@/components/chat/ChatInputBar";
import StarterQuestions from "@/components/chat/StarterQuestions";
import RecentSearchesChips from "@/components/search/RecentSearchesChips";
import MarkdownRenderer from "@/components/chat/MarkdownRenderer";
import { PageHeader } from "@/components/page-header";
import { MaintenanceService } from "@/lib/api/generated";
import { useSystemStatus } from "@/stores/app-store";
import Link from "next/link";
import { cn } from "@/lib/utils";

import { BRAIN_PLACEHOLDERS } from "@/lib/utils";
import { SystemStatusWarning } from "@/components/upload";

// Starter questions to help users get started (qualitative phrasing)
const starterQuestions = [
  {
    icon: FileText,
    text: "What key themes emerge in my August 2025 financial report?",
    category: "Analysis"
  },
  {
    icon: BarChart3,
    text: "Explain the AI architecture in the Q2 system design docs at a high level",
    category: "Technical"
  },
  {
    icon: MessageSquare,
    text: "For Project Orion, where are responsibilities and scope discussed?",
    category: "Legal"
  },
  {
    icon: Brain,
    text: "Find slide decks that outline product vision and strategy",
    category: "Business"
  }
];

const CHAT_PLACEHOLDER_EXAMPLES = [
  "Give a high-level overview of my latest project report",
  "What potential risks are highlighted in the compliance policies?",
  "Show conceptual diagrams about AI systems from the design docs",
  "Which vendor contracts discuss obligations?"
];

export default function ChatPage() {
  const {
    input,
    setInput,
    messages,
    loading,
    error,
    timeToFirstTokenMs,
    k,
    setK,
    toolCallingEnabled,
    setToolCallingEnabled,
    topK,
    setTopK,
    maxTokens,
    setMaxTokens,
    imageGroups,
    isSettingsValid,
    sendMessage,
    reset,
  } = useChat();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const [lightboxOpen, setLightboxOpen] = useState(false);
  const [lightboxSrc, setLightboxSrc] = useState("");
  const [lightboxAlt, setLightboxAlt] = useState<string | undefined>(undefined);
  const [uiSettingsValid, setUiSettingsValid] = useState(true);
  const [recentSearches, setRecentSearches] = useState<string[]>([]);
  const [requestStart, setRequestStart] = useState<number | null>(null);
  const [lastResponseDurationMs, setLastResponseDurationMs] = useState<number | null>(null);
  const [brainIdx, setBrainIdx] = useState<number>(0);
  const [sourceInspectorOpen, setSourceInspectorOpen] = useState(false);
  const [isClearing, setIsClearing] = useState(false);
  const { systemStatus, setStatus, isReady, needsRefresh } = useSystemStatus();
  const [statusLoading, setStatusLoading] = useState(false);
  const hasFetchedRef = useRef(false);
  const [placeholderIdx, setPlaceholderIdx] = useState(0);

  const scrollToBottom = () => {
    if (messagesContainerRef.current) {
      // Use rAF to ensure DOM has settled before scrolling
      requestAnimationFrame(() => {
        if (messagesContainerRef.current) {
          const viewport = messagesContainerRef.current.querySelector('[data-slot="scroll-area-viewport"]');
          if (viewport) {
            viewport.scrollTop = viewport.scrollHeight;
          }
        }
      });
    }
  };

  // Fetch system status function - always fetches fresh when called
  const fetchSystemStatus = useCallback(async () => {
    setStatusLoading(true);
    try {
      const status = await MaintenanceService.getStatusStatusGet();
      setStatus({ ...status, lastChecked: Date.now() });
      hasFetchedRef.current = true;
    } catch (err) {
      console.error('Failed to fetch system status:', err);
    } finally {
      setStatusLoading(false);
    }
  }, [setStatus]);

  // Fetch system status on mount and listen for changes
  useEffect(() => {
    // Only fetch if we haven't fetched yet
    if (!hasFetchedRef.current) {
      fetchSystemStatus();
    }

    // Listen for system status changes from other pages
    window.addEventListener('systemStatusChanged', fetchSystemStatus);
    
    return () => {
      window.removeEventListener('systemStatusChanged', fetchSystemStatus);
    };
  }, [fetchSystemStatus]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    const id = setInterval(() => setPlaceholderIdx((i) => (i + 1) % CHAT_PLACEHOLDER_EXAMPLES.length), 5000);
    return () => clearInterval(id);
  }, []);

  // Rotate "thinking" placeholders while loading
  useEffect(() => {
    if (loading) {
      // randomize start for variety
      setBrainIdx((prev) => (prev + Math.floor(Math.random() * BRAIN_PLACEHOLDERS.length)) % BRAIN_PLACEHOLDERS.length);
      const id = setInterval(() => {
        setBrainIdx((i) => (i + 1) % BRAIN_PLACEHOLDERS.length);
      }, 1200);
      return () => clearInterval(id);
    }
  }, [loading]);

  // sendMessage now provided by useChat
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!isSettingsValid || !uiSettingsValid) return;
    
    // Check if system is ready
    if (!isReady) {
      toast.error('System Not Ready', { 
        description: 'Initialize collection and bucket before using chat' 
      });
      return;
    }
    
    const q = input.trim();
    if (!q) return;
    // track start and recent searches
    setRequestStart(performance.now());
    setLastResponseDurationMs(null);
    setRecentSearches((prev) => {
      const updated = [q, ...prev.filter((s) => s !== q)].slice(0, 10);
      localStorage.setItem("colpali-chat-recent", JSON.stringify(updated));
      return updated;
    });
    sendMessage(e);
  };

  const messageVariants = {
    initial: { opacity: 0, y: 10, scale: 0.95 },
    animate: { opacity: 1, y: 0, scale: 1 },
    exit: { 
      opacity: 0, 
      y: -20, 
      scale: 0.9
    }
  };

  // Load recent searches from localStorage once
  useEffect(() => {
    const saved = localStorage.getItem("colpali-chat-recent");
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        setRecentSearches(Array.isArray(parsed) ? parsed.slice(0, 10) : []);
      } catch { }
    }
  }, []);

  // When an assistant message appears after a started request, compute duration
  useEffect(() => {
    if (requestStart && messages.length > 0) {
      const last = messages[messages.length - 1];
      if (last.role === "assistant") {
        setLastResponseDurationMs(performance.now() - requestStart);
        setRequestStart(null);
      }
    }
  }, [messages, requestStart]);

  return (
    <motion.div {...defaultPageMotion} className="page-shell flex flex-col min-h-0 flex-1 gap-6">
      <motion.section variants={sectionVariants} className="flex flex-col items-center text-center gap-6 pt-6 sm:pt-8">
      <PageHeader
          title="AI Chat"
          icon={Brain}
          tooltip="Ask questions about your documents and get AI-powered responses with inline citations"
        />
      </motion.section>
      <motion.section variants={sectionVariants} className="flex-1 min-h-0 flex flex-col gap-6 pb-6 sm:pb-8">
        <div className="mx-auto flex h-full w-full max-w-5xl flex-1 flex-col gap-6">
          {/* System Status Warning */}
          <SystemStatusWarning isReady={isReady} />
          {/* Chat Messages */}
          <Card className="card-surface mx-auto w-full max-w-4xl flex min-h-0 flex-1 flex-col overflow-hidden">
            <ScrollArea
              ref={messagesContainerRef}
              className="h-[calc(100vh-25rem)] rounded-xl">
              <div className="space-y-6 p-3 sm:p-4">
                <AnimatePresence mode="popLayout">
                {messages.length === 0 ? (
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="flex flex-col items-center justify-center h-full text-center py-2"
              >
                <div className="mb-4">
                  <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-blue-500 via-purple-500 to-cyan-500 shadow-lg">
                    <Brain className="h-6 w-6 text-white" />
                  </div>
                  <h2 className="text-xl font-semibold bg-gradient-to-r from-blue-600 via-purple-600 to-cyan-600 bg-clip-text text-transparent">Start Your Conversation</h2>
                </div>

                {/* Starter Questions */}
                <StarterQuestions questions={starterQuestions} onSelect={(t) => setInput(t)} />
                <div className="mt-3 w-full max-w-2xl">
                  <RecentSearchesChips
                    recentSearches={recentSearches}
                    visible
                    onSelect={(q) => setInput(q)}
                    onRemove={(q) => {
                      const updated = recentSearches.filter((s) => s !== q);
                      setRecentSearches(updated);
                      localStorage.setItem("colpali-chat-recent", JSON.stringify(updated));
                    }}
                  />
                </div>
              </motion.div>
                ) : (
              messages.map((message, idx) => (
                <motion.div
                  key={message.id || idx}
                  variants={messageVariants}
                  initial="initial"
                  animate={isClearing ? "exit" : "animate"}
                  exit="exit"
                  transition={{
                    duration: 0.3,
                    delay: isClearing ? idx * 0.08 : 0,
                  }}
                  className={`flex gap-4 mb-6 last:mb-0 ${message.role === "assistant" ? "" : "flex-row-reverse"}`}
                >
                  <div
                    className={cn(
                      "flex size-10 shrink-0 items-center justify-center rounded-full border-2 text-sm font-semibold shadow-lg",
                      message.role === "assistant"
                        ? "bg-gradient-to-br from-blue-500 via-purple-500 to-cyan-500 border-transparent text-white"
                        : "bg-gradient-to-br from-primary/90 to-primary border-transparent text-primary-foreground"
                    )}
                  >
                    {message.role === "assistant" ? (
                      <Brain className="h-5 w-5" />
                    ) : (
                      <User className="h-5 w-5" />
                    )}
                  </div>

                  <div className={cn("flex-1 max-w-[85%]", message.role === "user" && "text-right")}>
                    <div
                      className={cn(
                        "inline-block max-w-2xl rounded-2xl border px-5 py-3.5 text-left shadow-[var(--shadow-2)]",
                        message.role === "assistant"
                          ? "bg-gradient-to-br from-blue-500/5 via-purple-500/5 to-cyan-500/5 border-muted/60 backdrop-blur-sm"
                          : "bg-gradient-to-br from-primary/15 to-primary/10 border-primary/30 text-foreground"
                      )}
                    >
                      {message.content ? (
                        message.role === "assistant" ? (
                          <div className="text-[15px] leading-7">
                            <MarkdownRenderer 
                              content={message.content}
                              images={message.citations || []}
                              onImageClick={(url, label) => {
                                setLightboxSrc(url);
                                setLightboxAlt(label || 'Citation image');
                                setLightboxOpen(true);
                              }}
                            />
                          </div>
                        ) : (
                          <div className="whitespace-pre-wrap text-[15px] leading-7">{message.content}</div>
                        )
                      ) : (
                        loading && message.role === "assistant" ? (
                          <div className="flex items-center gap-3 text-muted-foreground">
                            <div className="relative">
                              <Loader2 className="w-5 h-5 animate-spin text-purple-500" />
                              <div className="absolute inset-0 blur-sm">
                                <Loader2 className="w-5 h-5 animate-spin text-purple-400" />
                              </div>
                            </div>
                            <AnimatePresence mode="wait" initial={false}>
                              <motion.span
                                key={brainIdx}
                                initial={{ opacity: 0, y: 4 }}
                                animate={{ opacity: 1, y: 0 }}
                                exit={{ opacity: 0, y: -4 }}
                                transition={{ duration: 0.2 }}
                                className="text-sm font-medium"
                              >
                                {BRAIN_PLACEHOLDERS[brainIdx]}
                              </motion.span>
                            </AnimatePresence>
                          </div>
                        ) : null
                      )}
                    </div>

                    {message.role === "assistant" && message.content && (
                      <div className="flex items-center gap-2 text-xs text-muted-foreground mt-2.5 ml-1">
                        <div className="flex items-center gap-1.5">
                          <div className="flex h-5 w-5 items-center justify-center rounded-full bg-gradient-to-br from-blue-500 via-purple-500 to-cyan-500">
                            <Brain className="h-3 w-3 text-white" />
                          </div>
                          <span className="font-medium">AI Assistant</span>
                        </div>
                        <div className="flex gap-0.5 ml-1">
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <Button variant="ghost" size="icon" className="h-6 w-6 hover:bg-green-500/10 hover:text-green-600 transition-colors" onClick={() => { /* TODO: thumbs up handler */ }}>
                                <span aria-hidden className="text-sm">👍</span>
                                <span className="sr-only">Mark helpful</span>
                              </Button>
                            </TooltipTrigger>
                            <TooltipContent>Mark as helpful</TooltipContent>
                          </Tooltip>
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <Button variant="ghost" size="icon" className="h-6 w-6 hover:bg-red-500/10 hover:text-red-600 transition-colors" onClick={() => { /* TODO: thumbs down handler */ }}>
                                <span aria-hidden className="text-sm">👎</span>
                                <span className="sr-only">Mark unhelpful</span>
                              </Button>
                            </TooltipTrigger>
                            <TooltipContent>Mark as unhelpful</TooltipContent>
                          </Tooltip>
                        </div>
                      </div>
                    )}
                  </div>
                </motion.div>
              ))
                )}
                </AnimatePresence>
                <div ref={messagesEndRef} />
              </div>
            </ScrollArea>

        {/* Input Form */}
        <div className="sticky bottom-0 left-0 right-0 border-t border-divider/50 bg-[color:var(--surface-0)]/95 px-4 py-3.5 backdrop-blur-lg supports-[backdrop-filter]:backdrop-blur">
          <ChatInputBar
            input={input}
            setInput={setInput}
            placeholder={`Ask anything about your documents... e.g., "${CHAT_PLACEHOLDER_EXAMPLES[placeholderIdx]}"`}
            loading={loading}
            isSettingsValid={isSettingsValid}
            uiSettingsValid={uiSettingsValid}
            setUiSettingsValid={setUiSettingsValid}
            onSubmit={handleSubmit}
            k={k}
            setK={setK}
            toolCallingEnabled={toolCallingEnabled}
            setToolCallingEnabled={setToolCallingEnabled}
            topK={topK}
            setTopK={setTopK}
            maxTokens={maxTokens}
            setMaxTokens={setMaxTokens}
            hasMessages={messages.length > 0}
            onClear={async () => {
              // Start clearing animation
              setIsClearing(true);
              
              // Wait for exit animations to complete
              await new Promise(resolve => setTimeout(resolve, 600));
              
              // Now actually clear the data
              reset();
              setInput('');
              setRequestStart(null);
              setLastResponseDurationMs(null);
              setIsClearing(false);
              
              toast.success('Conversation cleared', {
                description: 'Ready for a fresh start',
              });
            }}
          />

          {/* Tips below input */}
          <div className="mt-2.5 flex flex-wrap items-center gap-3 text-xs text-muted-foreground/80">
            <div className="flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5 text-purple-500" />
              <span>AI-powered with inline citations</span>
            </div>
            {timeToFirstTokenMs !== null && (
              <div className="flex items-center gap-1.5 rounded-full bg-[color:var(--surface-1)] px-2 py-0.5 border border-muted/40">
                <Clock className="w-3 h-3 text-green-500" />
                <span className="font-medium">{(timeToFirstTokenMs / 1000).toFixed(2)}s</span>
              </div>
            )}
          </div>

          {error && (
            <motion.div
              variants={fadeInPresence}
              initial="hidden"
              animate="visible"
              className="mt-3"
            >
              <Alert variant="destructive">
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            </motion.div>
          )}
        </div>
          </Card>
        </div>
      </motion.section>
      <ImageLightbox
        open={lightboxOpen}
        src={lightboxSrc}
        alt={lightboxAlt}
        onOpenChange={setLightboxOpen}
      />
    </motion.div>
  );
}