"use client";

import { useState, useRef, useEffect } from "react";
import { useChat } from "@/lib/hooks/use-chat";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
// Removed Select in favor of a clearer segmented control
import { Alert, AlertDescription } from "@/components/ui/alert";
import { User, Image as ImageIcon, Loader2, Sparkles, Brain, FileText, BarChart3, MessageSquare, Clock, Trash2 } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { toast } from "@/components/ui/sonner";
import ImageLightbox from "@/components/lightbox";
import ChatInputBar from "@/components/chat/ChatInputBar";
import StarterQuestions from "@/components/chat/StarterQuestions";
import RecentSearchesChips from "@/components/search/RecentSearchesChips";
import MarkdownRenderer from "@/components/chat/MarkdownRenderer";
import { PageHeader } from "@/components/page-header";

import { BRAIN_PLACEHOLDERS } from "@/lib/utils";

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
  const examples = [
    "Give a high-level overview of my latest project report",
    "What potential risks are highlighted in the compliance policies?",
    "Show conceptual diagrams about AI systems from the design docs",
    "Which vendor contracts discuss obligations?"
  ];
  const [placeholderIdx, setPlaceholderIdx] = useState(0);

  const scrollToBottom = () => {
    if (messagesContainerRef.current) {
      // Use rAF to ensure DOM has settled before scrolling
      requestAnimationFrame(() => {
        if (messagesContainerRef.current) {
          messagesContainerRef.current.scrollTop = messagesContainerRef.current.scrollHeight;
        }
      });
    }
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    const id = setInterval(() => setPlaceholderIdx((i) => (i + 1) % examples.length), 5000);
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
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="flex flex-col flex-1 min-h-0"
    >
      <PageHeader
        title="AI Chat"
        description="Ask questions about your documents and get AI-powered responses with inline citations"
        icon={Brain}
      />

      {/* Chat Messages */}
      <Card className="flex-1 flex flex-col min-h-0 overflow-hidden border-2 border-purple-200/50 shadow-xl bg-white">
        <div ref={messagesContainerRef} className="flex-1 min-h-0 overflow-y-auto overscroll-contain p-4 sm:p-6 custom-scrollbar bg-gradient-to-br from-blue-50/20 via-white to-purple-50/20">
          <AnimatePresence mode="popLayout">
            {messages.length === 0 ? (
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="flex flex-col items-center justify-center h-full text-center py-6"
              >

                <h2 className="text-2xl font-semibold mb-3 bg-gradient-to-r from-blue-600 via-purple-600 to-cyan-600 bg-clip-text text-transparent">Start Your Conversation</h2>
                <p className="text-muted-foreground max-w-lg mb-6 leading-relaxed">
                  Ask questions about your uploaded documents and get intelligent responses with visual proof from your content.
                </p>

                {/* Starter Questions */}
                <StarterQuestions questions={starterQuestions} onSelect={(t) => setInput(t)} />
                <div className="mt-4 w-full max-w-2xl">
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
                  className={`flex gap-3 mb-4 md:mb-5 last:mb-0 ${message.role === "assistant" ? "" : "flex-row-reverse"}`}
                >
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${message.role === "assistant"
                    ? "bg-gradient-to-br from-blue-600 to-purple-600 text-white shadow-lg border-2 border-purple-200/30"
                    : "bg-gradient-to-br from-blue-100 to-cyan-100 text-foreground shadow-lg border-2 border-blue-200/50"
                    }`}>
                    {message.role === "assistant" ? (
                      <Brain className="w-4 h-4" />
                    ) : (
                      <User className="w-4 h-4" />
                    )}
                  </div>

                  <div className={`flex-1 max-w-[85%] ${message.role === "user" ? "text-right" : ""
                    }`}>
                    <div className={`inline-block p-4 rounded-2xl shadow-md border-2 ${message.role === "assistant"
                      ? "bg-gradient-to-br from-blue-50 to-purple-50 text-foreground border-purple-200/50"
                      : "bg-gradient-to-br from-blue-100 to-cyan-100 text-foreground border-blue-200/50"
                      }`}>
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
                          <div className="flex items-center gap-2 text-muted-foreground">
                            <Loader2 className="w-4 h-4 animate-spin text-purple-500" />
                            <AnimatePresence mode="wait" initial={false}>
                              <motion.span
                                key={brainIdx}
                                initial={{ opacity: 0, y: 4 }}
                                animate={{ opacity: 1, y: 0 }}
                                exit={{ opacity: 0, y: -4 }}
                                transition={{ duration: 0.2 }}
                                className="text-sm"
                              >
                                {BRAIN_PLACEHOLDERS[brainIdx]}
                              </motion.span>
                            </AnimatePresence>
                          </div>
                        ) : null
                      )}
                    </div>

                    {message.role === "assistant" && (
                      <div className="flex items-center gap-2 text-xs text-muted-foreground mt-2 ml-2">
                        <Brain className="w-3 h-3 text-purple-500" />
                        <span>AI Assistant</span>
                        <div className="flex">
                          <Button variant="ghost" size="icon" className="h-6 w-6" onClick={() => { /* TODO: thumbs up handler */ }}>
                            <span aria-hidden>👍</span>
                            <span className="sr-only">Mark helpful</span>
                          </Button>
                          <Button variant="ghost" size="icon" className="h-6 w-6" onClick={() => { /* TODO: thumbs down handler */ }}>
                            <span aria-hidden>👎</span>
                            <span className="sr-only">Mark unhelpful</span>
                          </Button>
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

        {/* Input Form */}
        <div className="border-t-2 border-purple-200/50 p-4 bg-gradient-to-r from-blue-50/70 via-purple-50/70 to-cyan-50/70 backdrop-blur-sm">
          <ChatInputBar
            input={input}
            setInput={setInput}
            placeholder={`Ask anything about your documents... e.g., "${examples[placeholderIdx]}"`}
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
          <div className="mt-3 flex flex-wrap items-center gap-3 text-xs text-muted-foreground">
            <div className="flex items-center gap-1">
              <Sparkles className="w-3 h-3 text-purple-500" />
              <span>AI-powered responses with inline citations</span>
            </div>
            {timeToFirstTokenMs !== null && (
              <div className="flex items-center gap-1">
                <Clock className="w-3 h-3 text-muted-foreground" />
                <span>First token in {(timeToFirstTokenMs / 1000).toFixed(2)}s</span>
              </div>
            )}
          </div>

          {error && (
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              className="mt-3"
            >
              <Alert variant="destructive">
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            </motion.div>
          )}
        </div>
      </Card>
      <ImageLightbox
        open={lightboxOpen}
        src={lightboxSrc}
        alt={lightboxAlt}
        onOpenChange={setLightboxOpen}
      />
    </motion.div>
  );
}
