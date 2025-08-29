"use client";

import { useState, useRef, useEffect } from "react";
import { useChat } from "@/lib/hooks/use-chat";
import { Card } from "@/components/ui/8bit/card";
import { Badge } from "@/components/ui/8bit/badge";
// Removed Select in favor of a clearer segmented control
import { Alert, AlertDescription } from "@/components/ui/8bit/alert";
import { ScrollArea } from "@/components/ui/8bit/scroll-area";
import { Image as ImageIcon, Sparkles, Brain, FileText, BarChart3, MessageSquare, Clock, User, Loader2, Send, Eye } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import ImageLightbox from "@/components/lightbox";
import ChatInputBar from "@/components/chat/ChatInputBar";
import StarterQuestions from "@/components/chat/StarterQuestions";
import RecentSearchesChips from "@/components/search/RecentSearchesChips";
import { BRAIN_PLACEHOLDERS } from "@/lib/utils";
import Dialogue from "@/components/ui/8bit/blocks/dialogue";
import { cn } from "@/lib/utils";

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
    imageGroups,
    isSettingsValid,
    sendMessage,
  } = useChat();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const imagesSectionRef = useRef<HTMLDivElement>(null);
  const [lightboxOpen, setLightboxOpen] = useState(false);
  const [lightboxSrc, setLightboxSrc] = useState("");
  const [lightboxAlt, setLightboxAlt] = useState<string | undefined>(undefined);
  const [uiSettingsValid, setUiSettingsValid] = useState(true);
  const [recentSearches, setRecentSearches] = useState<string[]>([]);
  const [requestStart, setRequestStart] = useState<number | null>(null);
  const [lastResponseDurationMs, setLastResponseDurationMs] = useState<number | null>(null);
  const [brainIdx, setBrainIdx] = useState<number>(0);
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
    initial: { opacity: 0, y: 10 },
    animate: { opacity: 1, y: 0 },
    exit: { opacity: 0, y: -10 }
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
      className="flex flex-col h-[calc(100vh-6rem)] max-w-5xl mx-auto"
    >
      {/* Header */}
      <div className="flex-shrink-0 space-y-4 mb-6">
        <div className="flex items-center gap-4">
          <div className="p-3 bg-gradient-to-br from-accent/10 to-ring/10 rounded-lg border border-accent/20">
            <Brain className="w-8 h-8 text-accent" />
          </div>
          <div>
            <h1 className="text-4xl font-bold bg-gradient-to-r from-accent to-ring bg-clip-text text-transparent">AI Chat</h1>
            <p className="text-muted-foreground text-xl">Ask questions about your documents using natural language</p>
          </div>
        </div>

        {/* Quick Stats */}
        <div className="flex items-center gap-6 text-base text-muted-foreground">
          <div className="flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-accent" />
            <span>AI-powered responses</span>
          </div>
          <div className="flex items-center gap-2">
            <MessageSquare className="w-5 h-5 text-ring" />
            <span>Context-aware conversations</span>
          </div>
        </div>
      </div>

      {/* Chat Messages */}
      <div className="flex-1 overflow-hidden bg-gradient-to-b from-background to-muted/5 rounded-xl border border-border shadow-inner">
        <div className="h-full p-6 overflow-y-auto">
          <div className="space-y-6">
            {messages.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full py-16 text-center">
                <div className="w-20 h-20 bg-gradient-to-br from-accent/10 to-ring/10 rounded-lg flex items-center justify-center mb-6 border border-accent/20">
                  <Brain className="w-10 h-10 text-accent" />
                </div>
                <h3 className="text-3xl font-semibold mb-4">Start a conversation</h3>
                <p className="text-muted-foreground max-w-lg mb-8 text-xl leading-relaxed">
                  Ask me anything about your uploaded documents. I can help you find information, summarize content, or answer specific questions.
                </p>

                {/* Starter Questions */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-4xl">
                  {starterQuestions.map((question, idx) => (
                    <motion.button
                      key={idx}
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      onClick={() => setInput(question.text)}
                      className="p-6 text-left bg-card hover:bg-accent/5 rounded-lg border border-border hover:border-accent/30 transition-all duration-200 group"
                    >
                      <div className="flex items-start gap-4">
                        <div className="p-3 bg-accent/10 rounded border border-accent/20 group-hover:bg-accent/20 transition-colors">
                          <question.icon className="w-5 h-5 text-accent" />
                        </div>
                        <div className="flex-1">
                          <div className="font-medium text-foreground mb-2 text-base leading-relaxed">{question.text}</div>
                          <div className="text-sm text-muted-foreground">{question.category}</div>
                        </div>
                      </div>
                    </motion.button>
                  ))}
                </div>

                <div className="mt-8 w-full max-w-4xl">
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
              </div>
            ) : (
              <AnimatePresence>
                {messages.map((message, idx) => (
                  <motion.div
                    key={idx}
                    variants={messageVariants}
                    initial="initial"
                    animate="animate"
                    exit="exit"
                    className="mb-4 md:mb-5 last:mb-0"
                  >
                    <Dialogue
                      player={message.role === "assistant"}
                      avatarFallback={message.role === "assistant" ? "AI" : "You"}
                      title={message.role === "assistant" ? "AI Assistant" : "You"}
                      description={message.content || (loading && message.role === "assistant" ? BRAIN_PLACEHOLDERS[brainIdx] : "")}
                      className={cn(message.role !== "assistant" && "justify-end")}
                    />
                  </motion.div>
                ))}
              </AnimatePresence>
            )}
          </div>
        </div>
      </div>

      {/* Chat Input */}
      <div className="flex-shrink-0 mt-6">
        <Card className="border-2 border-accent/20 shadow-lg">
          <div className="p-6">
            <ChatInputBar
              input={input}
              setInput={setInput}
              onSubmit={handleSubmit}
              loading={loading}
              isSettingsValid={isSettingsValid}
              uiSettingsValid={uiSettingsValid}
              setUiSettingsValid={setUiSettingsValid}
              placeholder={examples[placeholderIdx]}
              k={k}
              setK={setK}
              toolCallingEnabled={toolCallingEnabled}
              setToolCallingEnabled={setToolCallingEnabled}
            />

            {error && (
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="mt-4"
              >
                <Alert variant="destructive">
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              </motion.div>
            )}
          </div>
        </Card>
      </div>
    </motion.div>
  );
}