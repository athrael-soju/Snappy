"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { AnimatePresence, motion } from "framer-motion";
import Image from "next/image";
import Link from "next/link";
import {
  Brain,
  FileText,
  Sparkles,
  Image as ImageIcon,
  AlertCircle,
} from "lucide-react";

import { useChat } from "@/lib/hooks/use-chat";
import { PageHeader } from "@/components/page-header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { ScrollArea } from "@/components/ui/scroll-area";
import ChatInputBar from "@/components/chat/ChatInputBar";
import MarkdownRenderer from "@/components/chat/MarkdownRenderer";
import ImageLightbox from "@/components/lightbox";
import { SystemStatusWarning } from "@/components/upload";
import { useSystemStatus } from "@/stores/app-store";
import { MaintenanceService } from "@/lib/api/generated";
import "@/lib/api/client";
import { toast } from "@/components/ui/sonner";

const SUGGESTIONS = [
  "Summarise the latest project update deck.",
  "What risks are noted in the compliance policy?",
  "Find slides that explain the product roadmap.",
  "Show invoices that mention infrastructure costs.",
] as const;

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
    isSettingsValid,
    sendMessage,
    reset,
  } = useChat();

  const { setStatus, isReady } = useSystemStatus();

  const [statusLoading, setStatusLoading] = useState(false);
  const [lightboxOpen, setLightboxOpen] = useState(false);
  const [lightboxSrc, setLightboxSrc] = useState("");
  const [lightboxAlt, setLightboxAlt] = useState<string | undefined>(undefined);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [uiSettingsValid, setUiSettingsValid] = useState(true);

  const hasMessages = messages.length > 0;

  const handleOpenLightbox = useCallback((src: string, alt?: string) => {
    setLightboxSrc(src);
    setLightboxAlt(alt);
    setLightboxOpen(true);
  }, []);

  const loadSystemStatus = useCallback(async () => {
    setStatusLoading(true);
    try {
      const status = await MaintenanceService.getStatusStatusGet();
      setStatus({ ...status, lastChecked: Date.now() });
    } catch (err) {
      console.error("Failed to load system status", err);
    } finally {
      setStatusLoading(false);
    }
  }, [setStatus]);

  useEffect(() => {
    loadSystemStatus();
    window.addEventListener("systemStatusChanged", loadSystemStatus);
    return () => window.removeEventListener("systemStatusChanged", loadSystemStatus);
  }, [loadSystemStatus]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const handleSubmit = useCallback(
    (event: React.FormEvent) => {
      event.preventDefault();
      if (!isReady) {
        toast.error("Snappy is still warming up", {
          description: "Initialize the backend services before sending a chat.",
        });
        return;
      }
      sendMessage(event);
    },
    [isReady, sendMessage],
  );

  return (
    <div className="flex min-h-screen flex-col">
      {/* Header Section */}
      <div className="border-b bg-gradient-to-br from-green-500/5 to-background px-6 py-12 sm:px-8 lg:px-12">
        <div className="mx-auto max-w-7xl">
          <div className="space-y-4">
            <div className="flex items-center gap-3">
              <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-green-500/10">
                <Brain className="h-6 w-6 text-green-600 dark:text-green-400" />
              </div>
              <div>
                <h1 className="text-3xl font-bold tracking-tight text-foreground sm:text-4xl">
                  AI Chat
                </h1>
                <p className="text-sm text-muted-foreground sm:text-base">
                  Ask questions and get answers with visual citations
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="mx-auto w-full max-w-7xl flex-1 px-6 py-8 sm:px-8 lg:px-12">
        <div className="flex h-[calc(100vh-220px)] flex-col gap-6">
          <SystemStatusWarning isReady={isReady} isLoading={statusLoading} className="rounded-2xl" />

          <Card className="flex flex-1 flex-col overflow-hidden border-2">
            <CardHeader className="border-b bg-muted/30 px-4 py-4 sm:px-6">
              <CardTitle className="text-lg font-semibold">Conversation</CardTitle>
            </CardHeader>
            <CardContent className="flex flex-1 flex-col gap-6 overflow-hidden p-4 sm:p-6">
              {!hasMessages && (
                <div className="space-y-4 rounded-lg border border-dashed border-muted p-6 text-sm text-muted-foreground">
                  <p className="font-medium text-foreground">Need inspiration? Try one of these prompts:</p>
                  <div className="flex flex-wrap gap-2">
                    {SUGGESTIONS.map((prompt) => (
                      <button
                        key={prompt}
                        type="button"
                        onClick={() => setInput(prompt)}
                        className="w-full rounded-full border border-muted px-4 py-2 text-left text-sm text-muted-foreground transition hover:border-primary hover:text-primary sm:w-auto"
                      >
                        {prompt}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              <ScrollArea className="flex-1">
                <div className="space-y-4 pr-2">
                  {messages.map((message) => (
                    <MessageBubble key={message.id} message={message} onPreview={handleOpenLightbox} />
                  ))}
                  <AnimatePresence>
                    {loading && (
                      <motion.div
                        initial={{ opacity: 0, y: 8 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: 8 }}
                        className="flex items-center gap-2 rounded-full bg-muted px-3 py-2 text-sm text-muted-foreground w-fit"
                      >
                        <Sparkles className="h-4 w-4 animate-pulse" />
                        Thinking...
                      </motion.div>
                    )}
                  </AnimatePresence>
                  <div ref={messagesEndRef} />
                </div>
              </ScrollArea>

              <div className="space-y-3 border-t border-muted pt-4 sm:pt-6">
                <ChatInputBar
                  input={input}
                  setInput={setInput}
                  placeholder="Ask anything about your documents..."
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
                  onClear={() => {
                    reset();
                    setInput("");
                    toast.success("Conversation cleared");
                  }}
                  hasMessages={hasMessages}
                />

                <div className="flex flex-wrap items-center gap-3 text-xs text-muted-foreground">
                  <span className="inline-flex items-center gap-1">
                    <Sparkles className="h-3.5 w-3.5 text-primary" />
                    Responses include citations
                  </span>
                  {timeToFirstTokenMs !== null && (
                    <span className="inline-flex items-center gap-1 rounded-full bg-muted px-2 py-0.5">
                      First token in {(timeToFirstTokenMs / 1000).toFixed(2)}s
                    </span>
                  )}
                  <Link href="/maintenance?section=configuration" className="underline">
                    Adjust model settings
                  </Link>
                </div>

                {error && (
                  <Alert variant="destructive">
                    <AlertCircle className="h-4 w-4" />
                    <AlertDescription>{error}</AlertDescription>
                  </Alert>
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      <ImageLightbox open={lightboxOpen} src={lightboxSrc} alt={lightboxAlt} onOpenChange={setLightboxOpen} />
    </div>
  );
}

function MessageBubble({
  message,
  onPreview,
}: {
  message: { id: string; role: "user" | "assistant"; content: string; citations?: Array<{ url: string | null; label: string | null; score: number | null }> };
  onPreview: (src: string, alt?: string) => void;
}) {
  const isAssistant = message.role === "assistant";

  const citations = message.citations ?? [];

  return (
    <div
      className={cnBubbleClass(isAssistant)}
      data-role={message.role}
    >
      <div className="flex items-center gap-2 text-xs font-medium text-muted-foreground">
        {isAssistant ? (
          <>
            <span className="inline-flex size-7 items-center justify-center rounded-full bg-primary/10 text-primary">
              <Brain className="h-4 w-4" />
            </span>
            <span>Snappy</span>
          </>
        ) : (
          <>
            <span className="inline-flex size-7 items-center justify-center rounded-full bg-secondary text-secondary-foreground">
              <FileText className="h-4 w-4" />
            </span>
            <span>You</span>
          </>
        )}
      </div>

      <div className="text-sm text-foreground">
        {isAssistant ? <MarkdownRenderer content={message.content} /> : <p>{message.content}</p>}
      </div>

      {isAssistant && citations.length > 0 && (
        <div className="space-y-2">
          <span className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
            Visual references
          </span>
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
            {citations.map((citation, index) => {
              const src = citation.url ?? (citation.label ?? "");
              const label = citation.label ?? `Reference ${index + 1}`;
              if (!src) {
                return (
                  <div
                    key={`${citation.label ?? index}-placeholder`}
                    className="flex h-24 items-center justify-center rounded-md border border-dashed border-muted text-xs text-muted-foreground"
                  >
                    <ImageIcon className="mr-1 h-4 w-4" />
                    Missing preview
                  </div>
                );
              }

              const isInline = src.startsWith("data:");

              return (
                <button
                  type="button"
                  key={`${citation.label ?? index}-${src}`}
                  onClick={() => onPreview(src, label)}
                  className="group relative h-24 overflow-hidden rounded-md border border-muted"
                >
                  <Image
                    src={src}
                    alt={label}
                    fill
                    className="object-cover transition-transform duration-300 group-hover:scale-105"
                    sizes="(max-width: 640px) 100vw, 33vw"
                    unoptimized={isInline}
                  />
                  <span className="absolute inset-x-0 bottom-0 bg-black/70 px-2 py-1 text-left text-[11px] font-medium text-white">
                    {label}
                  </span>
                </button>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

function cnBubbleClass(isAssistant: boolean) {
  return isAssistant
    ? "flex flex-col gap-3 rounded-lg border border-muted bg-card px-4 py-3 shadow-sm"
    : "ml-auto flex max-w-full flex-col gap-2 rounded-lg bg-primary text-primary-foreground px-4 py-2 shadow-sm sm:max-w-[80%]";
}
