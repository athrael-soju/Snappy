"use client";

import { useState, useRef, useEffect } from "react";
import type { ChatMessage } from "@/lib/api/generated";
import { ChatService, ApiError } from "@/lib/api/generated";
import { baseUrl } from "@/lib/api/client";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { Separator } from "@/components/ui/separator";
import { MessageSquare, Send, Bot, User, Image as ImageIcon, Loader2, Zap, Hash, Sparkles, Brain, HelpCircle, FileText, BarChart3 } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { toast } from "sonner";
import Image from "next/image";
import ImageLightbox from "@/components/lightbox";

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
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [stream, setStream] = useState<boolean>(true);
  const [k, setK] = useState<number>(5);
  const [imageGroups, setImageGroups] = useState<
    Array<{ url: string | null; label: string | null; score: number | null }[]>
  >([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const [lightboxOpen, setLightboxOpen] = useState(false);
  const [lightboxSrc, setLightboxSrc] = useState("");
  const [lightboxAlt, setLightboxAlt] = useState<string | undefined>(undefined);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  async function sendMessage(e: React.FormEvent) {
    e.preventDefault();
    const text = input.trim();
    if (!text) return;

    const userMsg: ChatMessage = { role: "user", content: text };
    const nextHistory: ChatMessage[] = [...messages, userMsg];
    setInput("");
    setLoading(true);
    setError(null);

    if (stream) {
      // Show placeholder assistant message for live updates
      setMessages([...nextHistory, { role: "assistant", content: "" }]);
      try {
        const res = await fetch(`${baseUrl}/chat/stream`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ message: text, chat_history: nextHistory, k }),
        });
        if (!res.body) {
          throw new Error("No response body for streaming");
        }
        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let assistantText = "";
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          assistantText += decoder.decode(value, { stream: true });
          setMessages((curr) => {
            if (curr.length === 0) return curr;
            const updated = [...curr];
            updated[updated.length - 1] = { role: "assistant", content: assistantText };
            return updated;
          });
        }
        // finalize decoder flush
        assistantText += new TextDecoder().decode();
        // Fetch retrieved images (non-AI path)
        try {
          const resImages = await fetch(`${baseUrl}/chat/stream`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: text, chat_history: messages, ai_enabled: false, k }),
          });
          if (resImages.ok) {
            const data = await resImages.json();
            const group = (data.images || []).map((img: any) => ({
              url: img.image_url ?? null,
              label: img.label ?? null,
              score: typeof img.score === "number" ? img.score : null,
            }));
            setImageGroups([group]);
          }
        } catch (e) {
          // Swallow image retrieval errors; streaming already succeeded
        }
      } catch (err: unknown) {
        let errorMsg = "Streaming failed";
        if (err instanceof ApiError) {
          errorMsg = `${err.status}: ${err.message}`;
        } else if (err instanceof Error) {
          errorMsg = err.message;
        }
        setError(errorMsg);
        toast.error("Chat Failed", { description: errorMsg });
      } finally {
        setLoading(false);
      }
      return;
    }

    // Non-streaming fallback using generated client
    setMessages(nextHistory);
    try {
      const res = await ChatService.chatChatPost({
        message: text,
        chat_history: messages,
        k,
      });
      const withAssistant: ChatMessage[] = [
        ...nextHistory,
        { role: "assistant", content: res.text },
      ];
      setMessages(withAssistant);
      const group = (res.images || []).map((img: any) => ({
        url: img.image_url ?? null,
        label: img.label ?? null,
        score: typeof img.score === "number" ? img.score : null,
      }));
      setImageGroups([group]);
      toast.success("Response received");
    } catch (err: unknown) {
      let errorMsg = "Chat failed";
      if (err instanceof ApiError) {
        errorMsg = `${err.status}: ${err.message}`;
      } else if (err instanceof Error) {
        errorMsg = err.message;
      }
      setError(errorMsg);
      toast.error("Chat Failed", { description: errorMsg });
    } finally {
      setLoading(false);
    }
  }

  const messageVariants = {
    initial: { opacity: 0, y: 10 },
    animate: { opacity: 1, y: 0 },
    exit: { opacity: 0, y: -10 }
  };

  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="flex flex-col h-[calc(100vh-12rem)] max-h-[800px]"
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
        
        <div className="flex items-center gap-4">
          <Tooltip>
            <TooltipTrigger asChild>
              <div className="flex items-center gap-2">
                <Hash className="w-4 h-4 text-muted-foreground" />
                <Select value={k.toString()} onValueChange={(value) => setK(parseInt(value, 10))} disabled={loading}>
                  <SelectTrigger className="w-20">
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
              <p>Number of search results to retrieve</p>
            </TooltipContent>
          </Tooltip>
          <Tooltip>
            <TooltipTrigger asChild>
              <div className="flex items-center gap-2">
                <Switch
                  id="stream-toggle"
                  checked={stream}
                  onCheckedChange={setStream}
                  disabled={loading}
                />
                <Label htmlFor="stream-toggle" className="text-sm font-medium cursor-pointer flex items-center gap-1">
                  <Zap className="w-4 h-4" />
                  Stream responses
                </Label>
              </div>
            </TooltipTrigger>
            <TooltipContent>
              <p>Enable real-time streaming of AI responses</p>
            </TooltipContent>
          </Tooltip>
        </div>
      </div>

      {/* Chat Messages */}
      <Card className="flex-1 flex flex-col overflow-hidden border-2 border-purple-100/50 shadow-lg">
        <div className="flex-1 overflow-y-auto p-4">
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
                <div className="w-full max-w-2xl space-y-4">
                  <div className="flex items-center gap-2 mb-4">
                    <HelpCircle className="w-5 h-5 text-purple-500" />
                    <span className="text-sm font-medium text-muted-foreground">Try asking:</span>
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    {starterQuestions.map((question, idx) => {
                      const Icon = question.icon;
                      return (
                        <motion.button
                          key={idx}
                          whileHover={{ scale: 1.02, y: -2 }}
                          whileTap={{ scale: 0.98 }}
                          onClick={() => setInput(question.text)}
                          className="p-4 text-left rounded-xl border-2 border-dashed border-purple-200 hover:border-purple-400 hover:bg-purple-50/30 transition-all group"
                        >
                          <div className="flex items-start gap-3">
                            <div className="p-2 bg-purple-100 rounded-lg group-hover:bg-purple-200 transition-colors">
                              <Icon className="w-4 h-4 text-purple-600" />
                            </div>
                            <div className="flex-1">
                              <p className="text-sm font-medium text-foreground group-hover:text-purple-700 transition-colors">
                                {question.text}
                              </p>
                              <Badge variant="outline" className="text-xs mt-2 group-hover:border-purple-300">
                                {question.category}
                              </Badge>
                            </div>
                          </div>
                        </motion.button>
                      );
                    })}
                  </div>
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
                  className={`flex gap-3 ${message.role === "assistant" ? "" : "flex-row-reverse"}`}
                >
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                    message.role === "assistant" 
                      ? "bg-gradient-to-br from-purple-500 to-pink-500 text-white shadow-lg" 
                      : "bg-gradient-to-br from-blue-500 to-cyan-500 text-white shadow-lg"
                  }`}>
                    {message.role === "assistant" ? (
                      <Brain className="w-4 h-4" />
                    ) : (
                      <User className="w-4 h-4" />
                    )}
                  </div>
                  
                  <div className={`flex-1 max-w-[85%] ${
                    message.role === "user" ? "text-right" : ""
                  }`}>
                    <div className={`inline-block p-4 rounded-2xl shadow-sm border ${
                      message.role === "assistant"
                        ? "bg-gradient-to-br from-purple-50 to-pink-50 text-foreground border-purple-200/50"
                        : "bg-gradient-to-br from-blue-500 to-cyan-500 text-white border-blue-300"
                    }`}>
                      <div className="whitespace-pre-wrap text-sm leading-relaxed">
                        {message.content || (loading && message.role === "assistant" ? (
                          <div className="flex items-center gap-2 text-muted-foreground">
                            <Loader2 className="w-4 h-4 animate-spin" />
                            <span>Thinking...</span>
                          </div>
                        ) : "")}
                      </div>
                    </div>
                    
                    {message.role === "assistant" && (
                      <div className="flex items-center gap-2 text-xs text-muted-foreground mt-2 ml-2">
                        <Brain className="w-3 h-3 text-purple-500" />
                        <span>AI Assistant</span>
                        {stream && <Badge variant="outline" className="text-xs">Streaming</Badge>}
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
          <form onSubmit={sendMessage} className="flex gap-3">
            <div className="flex-1 relative">
              <MessageSquare className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-muted-foreground" />
              <Input
                ref={inputRef}
                placeholder="Ask anything about your documents... Try: 'What are the key points in my reports?'"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                disabled={loading}
                className={`flex-1 text-base pl-11 h-12 border-2 transition-all ${
                  input.trim() 
                    ? 'border-purple-400 bg-white shadow-md focus:border-purple-500' 
                    : 'border-muted-foreground/20 focus:border-purple-400'
                }`}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    sendMessage(e);
                  }
                }}
              />
            </div>
            <Button 
              type="submit" 
              disabled={loading || !input.trim()}
              size="lg"
              className="px-6 h-12 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 shadow-lg"
            >
              {loading ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                </>
              ) : (
                <>
                  <Send className="w-5 h-5" />
                </>
              )}
            </Button>
          </form>
          
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
            <div className="flex items-center gap-2 mb-3">
              <div className="p-1 bg-purple-100 rounded">
                <ImageIcon className="h-4 w-4 text-purple-600" />
              </div>
              <span className="text-sm font-medium">Visual Citations</span>
              <Badge variant="secondary" className="bg-purple-100 text-purple-800">{imageGroups.flat().length} sources</Badge>
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
