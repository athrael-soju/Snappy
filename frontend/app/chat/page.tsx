"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { useChat } from "@/lib/hooks/use-chat";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tooltip, TooltipContent, TooltipTrigger, TooltipProvider } from "@/components/ui/tooltip";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { User, Loader2, Sparkles, Brain, FileText, BarChart3, MessageSquare, Clock, ThumbsUp, ThumbsDown } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { fadeInPresence } from "@/lib/motion-presets";
import { toast } from "sonner";
import ImageLightbox from "@/components/lightbox";
import ChatInputBar from "@/components/chat/ChatInputBar";
import StarterQuestions from "@/components/chat/StarterQuestions";
import MarkdownRenderer from "@/components/chat/MarkdownRenderer";
import { AppPage } from "@/components/layout";
import { MaintenanceService } from "@/lib/api/generated";
import { useSystemStatus } from "@/stores/app-store";
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
  const [requestStart, setRequestStart] = useState<number | null>(null);
  const [lastResponseDurationMs, setLastResponseDurationMs] = useState<number | null>(null);
  const [brainIdx, setBrainIdx] = useState<number>(0);
  const [sourceInspectorOpen, setSourceInspectorOpen] = useState(false);
  const [isClearing, setIsClearing] = useState(false);
  const { systemStatus, setStatus, isReady, needsRefresh } = useSystemStatus();
  const [statusLoading, setStatusLoading] = useState(false);
  const hasFetchedRef = useRef(false);
  const [placeholderIdx, setPlaceholderIdx] = useState(0);

  const handleClearConversation = useCallback(async () => {
    setIsClearing(true);

    await new Promise((resolve) => setTimeout(resolve, 600));

    reset();
    setInput("");
    setRequestStart(null);
    setLastResponseDurationMs(null);
    setIsClearing(false);

    toast.success("Conversation cleared", {
      description: "Ready for a fresh start",
    });
  }, [reset, setInput, setRequestStart, setLastResponseDurationMs]);

  const headerActions = (
    <Button
      variant="outline"
      size="sm"
      onClick={handleClearConversation}
      disabled={isClearing}
    >
      New Chat
    </Button>
  );


  const scrollToBottom = () => {
    if (messagesContainerRef.current) {
      requestAnimationFrame(() => {
        if (messagesContainerRef.current) {
          messagesContainerRef.current.scrollTop = messagesContainerRef.current.scrollHeight;
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
    // track start
    setRequestStart(performance.now());
    setLastResponseDurationMs(null);
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
    <AppPage
      title="Chat"
      description="Ask questions about your documents and receive grounded AI answers."
      actions={headerActions}
      contentClassName="stack stack-lg h-full"
    >
      <SystemStatusWarning isReady={isReady} />
      <TooltipProvider>
        <div className="page-surface flex h-full flex-col gap-4 overflow-hidden p-4 sm:p-6">
          <div className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-border/60 bg-muted/10 p-3 sm:p-4">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-blue-500 via-purple-500 to-cyan-500 text-white">
                <Brain className="h-5 w-5" />
              </div>
              <div className="space-y-1">
                <p className="text-sm font-medium text-foreground">Document Chat</p>
                <p className="text-xs text-muted-foreground">
                  Converse with your knowledge base and cite answers with context.
                </p>
              </div>
            </div>
            {timeToFirstTokenMs !== null && (
              <div className="flex items-center gap-1 rounded-full bg-muted px-2 py-0.5 text-xs text-muted-foreground">
                <Clock className="h-3 w-3 text-primary" />
                <span className="font-medium">{(timeToFirstTokenMs / 1000).toFixed(2)}s</span>
              </div>
            )}
          </div>

          <div
            ref={messagesContainerRef}
            className="flex-1 overflow-y-auto"
            style={{ overscrollBehavior: "contain", scrollbarGutter: "stable" }}
          >
            <div className="w-full px-2 sm:px-0">
              <AnimatePresence mode="popLayout">
                {messages.length === 0 ? (
                  <motion.div
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className="flex min-h-[320px] flex-col items-center justify-center text-center"
                  >
                    <div className="page-surface mx-auto w-full max-w-2xl space-y-6 p-6 sm:p-8" data-hover="true">
                      <div className="space-y-3">
                        <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-blue-500 via-purple-500 to-cyan-500 text-white sm:h-14 sm:w-14">
                          <Brain className="h-6 w-6 sm:h-7 sm:w-7" />
                        </div>
                        <h2 className="text-xl font-semibold sm:text-2xl">Start Your Conversation</h2>
                        <p className="text-sm text-muted-foreground sm:text-base">
                          Ask questions about your documents and get AI-powered responses with citations.
                        </p>
                      </div>
                      <StarterQuestions questions={starterQuestions} onSelect={setInput} />
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
                      className={cn(
                        "mb-4 flex gap-3 sm:mb-6 sm:gap-4",
                        message.role === "user" && "flex-row-reverse"
                      )}
                    >
                      <div
                        className={cn(
                          "flex size-8 shrink-0 items-center justify-center rounded-full shadow-md sm:size-10",
                          message.role === "assistant"
                            ? "bg-gradient-to-br from-blue-500 via-purple-500 to-cyan-500 text-white"
                            : "bg-primary text-primary-foreground"
                        )}
                      >
                        {message.role === "assistant" ? (
                          <Brain className="h-4 w-4 sm:h-5 sm:w-5" />
                        ) : (
                          <User className="h-4 w-4 sm:h-5 sm:w-5" />
                        )}
                      </div>

                      <div className={cn("min-w-0 flex-1", message.role === "user" && "flex justify-end")}>
                        <div
                          className={cn(
                            "inline-block max-w-full rounded-xl px-3 py-2.5 shadow-sm sm:max-w-[85%] sm:rounded-2xl sm:px-5 sm:py-3.5 lg:max-w-[640px]",
                            message.role === "assistant"
                              ? "border border-border bg-card text-foreground"
                              : "bg-primary text-primary-foreground"
                          )}
                        >
                          {message.content ? (
                            message.role === "assistant" ? (
                              <div className="leading-relaxed text-sm sm:text-base">
                                <MarkdownRenderer
                                  content={message.content}
                                  images={message.citations || []}
                                  onImageClick={(url, label) => {
                                    setLightboxSrc(url);
                                    setLightboxAlt(label || "Citation image");
                                    setLightboxOpen(true);
                                  }}
                                />
                              </div>
                            ) : (
                              <div className="whitespace-pre-wrap text-sm leading-relaxed sm:text-base">
                                {message.content}
                              </div>
                            )
                          ) : (
                            loading &&
                            message.role === "assistant" && (
                              <div className="flex items-center gap-2 text-muted-foreground sm:gap-3">
                                <Loader2 className="h-4 w-4 animate-spin text-primary sm:h-5 sm:w-5" />
                                <AnimatePresence mode="wait" initial={false}>
                                  <motion.span
                                    key={brainIdx}
                                    initial={{ opacity: 0, y: 4 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    exit={{ opacity: 0, y: -4 }}
                                    transition={{ duration: 0.2 }}
                                    className="text-xs font-medium sm:text-sm"
                                  >
                                    {BRAIN_PLACEHOLDERS[brainIdx]}
                                  </motion.span>
                                </AnimatePresence>
                              </div>
                            )
                          )}
                        </div>

                        {message.role === "assistant" && message.content && (
                          <div className="mt-2 ml-1 flex items-center gap-2 text-xs text-muted-foreground">
                            <div className="flex items-center gap-1.5">
                              <div className="flex h-4 w-4 items-center justify-center rounded-full bg-gradient-to-br from-blue-500 via-purple-500 to-cyan-500">
                                <Brain className="h-2.5 w-2.5 text-white" />
                              </div>
                              <span className="hidden font-medium sm:inline">AI Assistant</span>
                            </div>
                            <div className="flex gap-0.5">
                              <Tooltip>
                                <TooltipTrigger asChild>
                                  <Button
                                    variant="ghost"
                                    size="icon"
                                    className="h-5 w-5 sm:h-6 sm:w-6"
                                    onClick={() => {}}
                                  >
                                    <ThumbsUp className="h-3 w-3 sm:h-3.5 sm:w-3.5" />
                                    <span className="sr-only">Mark helpful</span>
                                  </Button>
                                </TooltipTrigger>
                                <TooltipContent>Helpful</TooltipContent>
                              </Tooltip>
                              <Tooltip>
                                <TooltipTrigger asChild>
                                  <Button
                                    variant="ghost"
                                    size="icon"
                                    className="h-5 w-5 sm:h-6 sm:w-6"
                                    onClick={() => {}}
                                  >
                                    <ThumbsDown className="h-3 w-3 sm:h-3.5 sm:w-3.5" />
                                    <span className="sr-only">Mark unhelpful</span>
                                  </Button>
                                </TooltipTrigger>
                                <TooltipContent>Not helpful</TooltipContent>
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
          </div>

          <div className="border-t border-border/60 pt-4">
            <ChatInputBar
              input={input}
              setInput={setInput}
              placeholder="Ask anything about your documents. Press Enter to send"
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
              onClear={handleClearConversation}
            />

            <div className="mt-2 flex flex-wrap items-center gap-2 text-xs text-muted-foreground sm:gap-3">
              <div className="flex items-center gap-1.5">
                <Sparkles className="h-3 w-3 text-primary sm:h-3.5 sm:w-3.5" />
                <span className="hidden sm:inline">AI-powered with inline citations</span>
                <span className="sm:hidden">AI-powered</span>
              </div>
              {timeToFirstTokenMs !== null && (
                <div className="flex items-center gap-1 rounded-full bg-muted px-2 py-0.5">
                  <Clock className="h-3 w-3 text-primary" />
                  <span className="font-medium">{(timeToFirstTokenMs / 1000).toFixed(2)}s</span>
                </div>
              )}
            </div>

            {error && (
              <motion.div variants={fadeInPresence} initial="hidden" animate="visible" className="mt-3">
                <Alert variant="destructive">
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              </motion.div>
            )}
          </div>
        </div>
      </TooltipProvider>
      <ImageLightbox open={lightboxOpen} src={lightboxSrc} alt={lightboxAlt} onOpenChange={setLightboxOpen} />
    </AppPage>
  );
}
