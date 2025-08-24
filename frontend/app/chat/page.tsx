"use client";

import { useState, useRef, useEffect } from "react";
import { useChat } from "@/lib/hooks/use-chat";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
// Removed Select in favor of a clearer segmented control
import { Alert, AlertDescription } from "@/components/ui/alert";
import { User, Image as ImageIcon, Loader2, Sparkles, Brain, FileText, BarChart3, MessageSquare } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import ImageLightbox from "@/components/lightbox";
import ChatInputBar from "@/components/chat/ChatInputBar";
import StarterQuestions from "@/components/chat/StarterQuestions";
import RecentSearchesChips from "@/components/search/RecentSearchesChips";
import { BRAIN_PLACEHOLDERS } from "@/lib/utils";

// Starter questions to help users get started
const starterQuestions = [
  {
    icon: FileText,
    text: "Summarize my uploaded financial reports",
    category: "Analysis"
  },
  {
    icon: BarChart3,
    text: "Find diagrams about AI architecture",
    category: "Technical"
  },
  {
    icon: MessageSquare,
    text: "What contracts mention payment terms?",
    category: "Legal"
  },
  {
    icon: Brain,
    text: "Show me presentation slides about product features",
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
    k,
    kMode,
    setK,
    setKMode,
    toolsEnabled,
    setToolsEnabled,
    model,
    setModel,
    imageGroups,
    isSettingsValid,
    sendMessage,
  } = useChat();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [lightboxOpen, setLightboxOpen] = useState(false);
  const [lightboxSrc, setLightboxSrc] = useState("");
  const [lightboxAlt, setLightboxAlt] = useState<string | undefined>(undefined);
  const [uiSettingsValid, setUiSettingsValid] = useState(true);
  const [recentSearches, setRecentSearches] = useState<string[]>([]);
  const [requestStart, setRequestStart] = useState<number | null>(null);
  const [lastResponseDurationMs, setLastResponseDurationMs] = useState<number | null>(null);
  const [brainIdx, setBrainIdx] = useState<number>(0);
  const examples = [
    "Summarize my last report",
    "What are the key risks?",
    "Find diagrams about AI architecture",
    "Which contracts mention payment terms?"
  ];
  const [placeholderIdx, setPlaceholderIdx] = useState(0);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
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
      const updated = [q, ...prev.filter((s) => s !== q)].slice(0, 8);
      localStorage.setItem("colpali-chat-recent", JSON.stringify(updated));
      return updated;
    });
    sendMessage(e);
  };

  const messageVariants = {
    initial: { opacity: 0, y: 10 },
    animate: { opacity: 1, y: 0 },
    exit: { opacity: 0, y: -10 }
  };

  // Load recent searches from localStorage once
  useEffect(() => {
    const saved = localStorage.getItem("colpali-chat-recent");
    if (saved) {
      try {
        setRecentSearches(JSON.parse(saved));
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
      className="flex flex-col h-[calc(100vh-12rem)] max-h-[825px]"
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-gradient-to-br from-purple-500/10 to-pink-500/10 rounded-lg border border-purple-500/20">
            <Brain className="w-6 h-6 text-purple-500" />
          </div>
          <div>
            <h1 className="text-3xl font-bold bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent">AI Chat</h1>
            <p className="text-muted-foreground text-lg">Ask questions about your documents and get AI-powered responses with visual citations</p>
          </div>
        </div>
      </div>

      {/* Chat Messages */}
      <Card className="flex-1 flex flex-col overflow-hidden border-2 border-purple-100/50 shadow-lg">
        <div className="flex-1 overflow-y-auto p-4">
          {messages.length > 0 && lastResponseDurationMs !== null && !loading && (
            <div className="flex justify-end mb-2 text-xs text-muted-foreground">Responded in {(lastResponseDurationMs / 1000).toFixed(2)}s</div>
          )}
          <AnimatePresence mode="popLayout">
            {messages.length === 0 ? (
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="flex flex-col items-center justify-center h-full text-center py-12"
              >
                <div className="w-20 h-20 bg-gradient-to-br from-purple-500/10 to-pink-500/10 rounded-full flex items-center justify-center mb-6 border border-purple-500/20">
                  <Brain className="w-10 h-10 text-purple-500" />
                </div>
                <h3 className="text-2xl font-bold mb-4 bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent">Start Your AI Conversation</h3>
                <p className="text-muted-foreground max-w-lg mb-8 text-lg leading-relaxed">
                  Ask questions about your uploaded documents and get intelligent responses with visual proof from your content.
                </p>

                {/* Starter Questions */}
                <StarterQuestions questions={starterQuestions} onSelect={(t) => setInput(t)} />
                <div className="mt-6 w-full max-w-2xl">
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
                  key={idx}
                  variants={messageVariants}
                  initial="initial"
                  animate="animate"
                  exit="exit"
                  className={`flex gap-3 mb-4 md:mb-5 last:mb-0 ${message.role === "assistant" ? "" : "flex-row-reverse"}`}
                >
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${message.role === "assistant"
                      ? "bg-gradient-to-br from-purple-500 to-pink-500 text-white shadow-lg"
                      : "bg-gradient-to-br from-blue-100 to-cyan-100 text-foreground shadow-lg"
                    }`}>
                    {message.role === "assistant" ? (
                      <Brain className="w-4 h-4" />
                    ) : (
                      <User className="w-4 h-4" />
                    )}
                  </div>

                  <div className={`flex-1 max-w-[85%] ${message.role === "user" ? "text-right" : ""
                    }`}>
                    <div className={`inline-block p-4 rounded-2xl shadow-sm border ${message.role === "assistant"
                        ? "bg-gradient-to-br from-purple-50 to-pink-50 text-foreground border-purple-200/50"
                        : "bg-gradient-to-br from-blue-100 to-cyan-100 text-foreground border-blue-200"
                      }`}>
                      {message.content ? (
                        message.role === "assistant" ? (
                          <div className="whitespace-pre-wrap text-[15px] leading-7">
                            {message.content.split("\n\n").map((para, i) => (
                              <p key={i} className="mb-3 last:mb-0">{para}</p>
                            ))}
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
        <div className="border-t border-purple-100/50 p-4 bg-gradient-to-r from-purple-50/30 to-pink-50/30">
          <ChatInputBar
            input={input}
            setInput={setInput}
            placeholder={`Ask anything about your documents... e.g., “${examples[placeholderIdx]}”`}
            loading={loading}
            isSettingsValid={isSettingsValid}
            uiSettingsValid={uiSettingsValid}
            setUiSettingsValid={setUiSettingsValid}
            onSubmit={handleSubmit}
            k={k}
            kMode={kMode}
            setK={setK}
            setKMode={setKMode}
            toolsEnabled={toolsEnabled}
            setToolsEnabled={setToolsEnabled}
            model={model}
            setModel={setModel}
          />

          {/* Tips below input */}
          <div className="mt-3 flex items-center gap-4 text-xs text-muted-foreground">
            <div className="flex items-center gap-1">
              <Sparkles className="w-3 h-3 text-purple-500" />
              <span>AI-powered responses</span>
            </div>
            <div className="flex items-center gap-1">
              <ImageIcon className="w-3 h-3 text-pink-500" />
              <span>Visual citations included</span>
            </div>
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

      {/* Retrieved Images */}
      <AnimatePresence>
        {imageGroups.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="bg-muted/50 rounded-lg p-3 max-h-64 overflow-y-auto"
          >
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <div className="p-1 bg-purple-100 rounded">
                  <ImageIcon className="h-4 w-4 text-purple-600" />
                </div>
                <span className="text-sm font-medium">Visual Citations</span>
                <Badge variant="secondary" className="bg-purple-100 text-purple-800">{imageGroups.flat().length} sources</Badge>
              </div>
              {/* Sources presets are now in the header for global visibility */}
            </div>
            <div className="grid grid-cols-4 md:grid-cols-6 lg:grid-cols-8 gap-1.5">
              {imageGroups.flat().map((img, idx) => (
                <motion.div
                  key={idx}
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: idx * 0.05 }}
                  className="relative group"
                >
                  {img.url && (
                    <img
                      src={img.url}
                      alt={img.label || `Image ${idx + 1}`}
                      className="w-full h-12 object-cover rounded border cursor-zoom-in"
                      onClick={() => {
                        setLightboxSrc(img.url!);
                        setLightboxAlt(img.label || `Image ${idx + 1}`);
                        setLightboxOpen(true);
                      }}
                    />
                  )}
                  <div className="pointer-events-none absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity rounded flex items-center justify-center">
                    <div className="text-white text-center p-1">
                      {img.label && (
                        <p className="text-xs font-medium truncate">{img.label}</p>
                      )}
                      {img.score && (
                        <Badge variant="secondary" className="mt-1 text-xs">
                          {img.score.toFixed(2)}
                        </Badge>
                      )}
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
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
