"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import "@/lib/api/client";
import { useChat } from "@/lib/hooks/use-chat";
import { useSystemStatus } from "@/stores/app-store";
import { useConfigStore } from "@/lib/config/config-store";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import ImageLightbox from "@/components/lightbox";
import { AlertCircle, Bot, Sparkles, Timer } from "lucide-react";
import { PageHeader } from "@/components/page-header";
import { SuggestionPanel } from "@/components/chat/suggestion-panel";
import { ChatMessageBubble } from "@/components/chat/chat-message";
import { ChatComposer } from "@/components/chat/chat-composer";

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
    reasoningEffort,
    setReasoningEffort,
    summaryPreference,
    setSummaryPreference,
    isSettingsValid,
    sendMessage,
    reset,
  } = useChat();
  const { isReady } = useSystemStatus();
  const config = useConfigStore((state) => state.config);

  // Check if heatmaps are enabled in config
  const heatmapsEnabled = config?.COLPALI_SHOW_HEATMAPS === 'True';

  // Track the most recent user query for heatmap generation
  const lastUserQuery = useMemo(() => {
    const userMessages = messages.filter((msg) => msg.role === 'user');
    return userMessages.length > 0 ? userMessages[userMessages.length - 1].content : null;
  }, [messages]);

  const [lightboxOpen, setLightboxOpen] = useState(false);
  const [lightboxSrc, setLightboxSrc] = useState<string>("");
  const [lightboxAlt, setLightboxAlt] = useState<string | null>(null);

  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const endOfMessagesRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    endOfMessagesRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages.length, loading]);

  const recentQuestions = useMemo(
    () =>
      messages
        .filter((msg) => msg.role === "user" && msg.content.trim().length > 0)
        .slice(-6)
        .reverse(),
    [messages],
  );

  const isSendDisabled = loading || !isReady || !input.trim() || !isSettingsValid;
  const hasMessages = messages.length > 0;

  const handleSuggestionClick = (prompt: string) => {
    setInput(prompt);
    textareaRef.current?.focus();
  };

  const handleCitationOpen = (url: string, label?: string | null) => {
    if (!url) {
      return;
    }
    setLightboxSrc(url);
    setLightboxAlt(label ?? null);
    setLightboxOpen(true);
  };

  return (
    <div className="relative flex min-h-full flex-1 flex-col overflow-hidden">
      <div className="flex h-full flex-1 flex-col overflow-hidden px-4 py-6 sm:px-6 lg:px-10">
        <motion.div
          className="mx-auto flex h-full w-full max-w-6xl flex-col gap-8"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, ease: "easeOut" }}
        >
          <motion.div
            className="shrink-0"
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1, duration: 0.3 }}
          >
            <PageHeader
              align="center"
              spacing="lg"
              title={
                <>
                  <span className="bg-gradient-to-br from-foreground via-foreground to-foreground/70 bg-clip-text text-transparent">
                    Chat with
                  </span>{" "}
                  <span className="bg-gradient-to-r from-chart-1 via-chart-2 to-chart-1 bg-clip-text text-transparent">
                    Snappy
                  </span>
                </>
              }
              description="Explore uploads with Snappy's grounded answers, inline citations, and visual cues from the ColPali stack."
              childrenClassName="gap-2 text-body-xs"
            >
              <Badge variant={isReady ? "default" : "destructive"} className="gap-1.5 px-3 py-1.5">
                {isReady ? (
                  <>
                    <Sparkles className="size-icon-sm text-primary-foreground" />
                    Connected to workspace
                  </>
                ) : (
                  <>
                    <AlertCircle className="size-icon-sm" />
                    Setup required
                  </>
                )}
              </Badge>
              {timeToFirstTokenMs !== null && (
                <Badge variant="secondary" className="gap-1.5 px-3 py-1.5">
                  <Timer className="size-icon-sm" />
                  {(timeToFirstTokenMs / 1000).toFixed(2)}s response time
                </Badge>
              )}
              {toolCallingEnabled && (
                <Badge variant="outline" className="gap-1.5 px-3 py-1.5 border-primary/30 text-primary">
                  <Bot className="size-icon-sm" />
                  Tool Calling Enabled
                </Badge>
              )}
            </PageHeader>
          </motion.div>

          <section className="relative flex min-h-[520px] flex-1 flex-col overflow-hidden">
            <div className="relative flex flex-1 overflow-hidden">
              <ScrollArea className="h-full w-full">
                <div className="space-y-6 px-6 pb-32 pr-4 sm:px-10">
                  <AnimatePresence initial={false}>
                    {!hasMessages && (
                      <motion.div
                        layout
                        className="flex justify-center"
                        initial={{ opacity: 0, y: 24 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -24 }}
                        transition={{ duration: 0.3, ease: "easeInOut" }}
                      >
                        <SuggestionPanel onSelect={handleSuggestionClick} recentQuestions={recentQuestions} />
                      </motion.div>
                    )}
                  </AnimatePresence>

                  <AnimatePresence mode="popLayout">
                    {messages.map((message, index) => {
                      const isLastMessage = index === messages.length - 1;
                      const isLastAssistantMessage = isLastMessage && message.role === "assistant";
                      return (
                        <ChatMessageBubble
                          key={message.id}
                          message={message}
                          query={lastUserQuery}
                          heatmapsEnabled={heatmapsEnabled}
                          isLoading={loading && isLastAssistantMessage}
                          onOpenCitation={handleCitationOpen}
                        />
                      );
                    })}
                  </AnimatePresence>

                  <AnimatePresence mode="wait">
                    {loading && !hasMessages && (
                      <ChatMessageBubble
                        key="loading"
                        message={{ id: "loading", role: "assistant", content: "" }}
                        query={lastUserQuery}
                        heatmapsEnabled={heatmapsEnabled}
                        isLoading={true}
                      />
                    )}
                  </AnimatePresence>
                  <div ref={endOfMessagesRef} />
                </div>
              </ScrollArea>
            </div>
          </section>

          <ChatComposer
            ref={textareaRef}
            input={input}
            onInputChange={setInput}
            isReady={isReady}
            loading={loading}
            isSendDisabled={isSendDisabled}
            toolCallingEnabled={toolCallingEnabled}
            onToolToggle={setToolCallingEnabled}
            k={k}
            onKChange={setK}
            reasoningEffort={reasoningEffort}
            onReasoningChange={setReasoningEffort}
            summaryPreference={summaryPreference}
            onSummaryChange={setSummaryPreference}
            isSettingsValid={isSettingsValid}
            sendMessage={sendMessage}
            error={error}
            onReset={reset}
            hasMessages={hasMessages}
          />
        </motion.div>
      </div>
      <ImageLightbox
        open={lightboxOpen}
        src={lightboxSrc}
        alt={lightboxAlt ?? undefined}
        onOpenChange={(open) => {
          setLightboxOpen(open);
          if (!open) {
            setLightboxSrc("");
            setLightboxAlt(null);
          }
        }}
      />
    </div>
  );
}
