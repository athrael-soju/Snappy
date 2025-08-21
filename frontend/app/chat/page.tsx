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
import { MessageSquare, Send, Bot, User, Image as ImageIcon, Loader2, Zap, Hash } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { toast } from "sonner";
import Image from "next/image";
import ImageLightbox from "@/components/lightbox";

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
          <div className="p-2 bg-purple-500/10 rounded-lg">
            <MessageSquare className="w-6 h-6 text-purple-500" />
          </div>
          <div>
            <h1 className="text-3xl font-bold">AI Chat</h1>
            <p className="text-muted-foreground">Ask questions about your documents</p>
          </div>
        </div>
        
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
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
          <div className="flex items-center gap-2">
            <input
              id="stream-toggle"
              type="checkbox"
              className="size-4 rounded border-border text-primary focus:ring-primary"
              checked={stream}
              onChange={(e) => setStream(e.target.checked)}
              disabled={loading}
            />
            <Label htmlFor="stream-toggle" className="text-sm font-medium cursor-pointer flex items-center gap-1">
              <Zap className="w-4 h-4" />
              Stream responses
            </Label>
          </div>
        </div>
      </div>

      {/* Chat Messages */}
      <Card className="flex-1 flex flex-col overflow-hidden">
        <div className="flex-1 overflow-y-auto p-4">
          <AnimatePresence mode="popLayout">
            {messages.length === 0 ? (
              <motion.div 
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="flex flex-col items-center justify-center h-full text-center py-12"
              >
                <div className="w-16 h-16 bg-muted rounded-full flex items-center justify-center mb-4">
                  <MessageSquare className="w-8 h-8 text-muted-foreground" />
                </div>
                <h3 className="text-lg font-medium mb-2">Start a conversation</h3>
                <p className="text-muted-foreground max-w-md">
                  Ask questions about your uploaded documents and get AI-powered responses with visual citations.
                </p>
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
                      ? "bg-primary text-primary-foreground" 
                      : "bg-muted"
                  }`}>
                    {message.role === "assistant" ? (
                      <Bot className="w-4 h-4" />
                    ) : (
                      <User className="w-4 h-4" />
                    )}
                  </div>
                  
                  <div className={`flex-1 max-w-[85%] ${
                    message.role === "user" ? "text-right" : ""
                  }`}>
                    <div className={`inline-block p-4 rounded-2xl ${
                      message.role === "assistant"
                        ? "bg-muted text-foreground"
                        : "bg-primary text-primary-foreground"
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
                      <div className="text-xs text-muted-foreground mt-2 ml-2">
                        AI Assistant
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
        <div className="border-t p-4">
          <form onSubmit={sendMessage} className="flex gap-2">
            <Input
              ref={inputRef}
              placeholder="Ask something about your documents..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              disabled={loading}
              className="flex-1 text-base"
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  sendMessage(e);
                }
              }}
            />
            <Button 
              type="submit" 
              disabled={loading || !input.trim()}
              size="lg"
              className="px-4"
            >
              {loading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Send className="w-4 h-4" />
              )}
            </Button>
          </form>
          
          {error && (
            <motion.div 
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              className="flex items-center gap-2 p-3 mt-3 bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-800 rounded-lg text-red-800 dark:text-red-200 text-sm"
              role="alert"
            >
              <span className="font-medium">{error}</span>
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
            <div className="flex items-center gap-2 mb-2">
              <ImageIcon className="h-4 w-4" />
              <span className="text-sm font-medium">Retrieved Images</span>
              <Badge variant="secondary">{imageGroups.flat().length} results</Badge>
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
