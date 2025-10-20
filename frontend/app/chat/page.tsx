"use client";

import Link from "next/link";
import { ChangeEvent, useEffect, useMemo, useRef, useState } from "react";
import type { FormEvent } from "react";
import { motion, AnimatePresence } from "framer-motion";
import "@/lib/api/client";
import { useChat } from "@/lib/hooks/use-chat";
import { useSystemStatus } from "@/stores/app-store";
import { ScrollArea } from "@/components/ui/scroll-area";
import { AppButton } from "@/components/app-button";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { getRandomBrainPlaceholder } from "@/lib/chat/brain-states";
import { cn } from "@/lib/utils";
import ImageLightbox from "@/components/lightbox";
import MarkdownRenderer from "@/components/chat/MarkdownRenderer";
import {
  AlertCircle,
  Bot,
  Clock3,
  MessageCircle,
  Send,
  Sparkles,
  Timer,
  User,
  Wand2,
  Telescope,
  ClipboardCheck,
  Settings,
  Trash2,
} from "lucide-react";
import { MortyLoader } from "@/components/morty-loader";
import { Popover, PopoverTrigger, PopoverContent } from "@/components/ui/popover";
import { RoutePageShell } from "@/components/route-page-shell";
import { HeroMetaGroup, HeroMetaPill } from "@/components/hero-meta";
import { MortyMetaCard } from "@/components/morty-meta-card";

const starterPrompts = [
  {
    title: "Ask Morty about visuals",
    description: "Let Morty search for charts, diagrams, or images showing specific data or concepts.",
    tag: "Visual",
    icon: Telescope,
    emoji: "🔍",
    prompt: "Morty, find all charts and diagrams related to [your topic] and describe what they show.",
  },
  {
    title: "Have Morty extract data",
    description: "Ask Morty to pull specific data from tables and structured content in documents.",
    tag: "Data",
    icon: ClipboardCheck,
    emoji: "📊",
    prompt: "Morty, what information is shown in the tables about [your topic]? List the key data points.",
  },
  {
    title: "Get Morty's layout insights",
    description: "Let Morty analyze how information is organized across pages and sections.",
    tag: "Layout",
    icon: MessageCircle,
    emoji: "📑",
    prompt: "Morty, describe the layout and structure of documents covering [your topic]. Where is the key information located?",
  },
  {
    title: "Ask Morty to compare",
    description: "Have Morty identify differences and similarities between images and diagrams.",
    tag: "Compare",
    icon: Wand2,
    emoji: "🔬",
    prompt: "Morty, compare the visual elements across different documents about [your topic]. What patterns or differences do you notice?",
  },
];

type StarterPromptItemProps = {
  item: (typeof starterPrompts)[0];
  onClick: (prompt: string) => void;
};

function StarterPromptItem({ item, onClick }: StarterPromptItemProps) {
  return (
    <motion.button
      key={item.prompt}
      type="button"
      onClick={() => onClick(item.prompt)}
      className="group relative overflow-hidden rounded-xl border border-border/20 bg-background/90 p-3 sm:p-4 text-left shadow-xs transition hover:border-primary/50 hover:shadow-md hover:shadow-primary/10 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/60 touch-manipulation"
      whileHover={{ scale: 1.02, y: -2 }}
      whileTap={{ scale: 0.98 }}
    >
      <div className="absolute inset-0 bg-gradient-to-br from-primary/10 via-transparent to-chart-1/5 opacity-0 transition group-hover:opacity-100" />
      <div className="relative flex flex-col gap-2">
        <div className="flex items-center justify-between gap-2">
          <div className="flex size-icon-lg flex-shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary shadow-sm">
            <item.icon className="size-icon-sm" />
          </div>
          <Badge variant="outline" className="flex-shrink-0 rounded-full border-primary/30 px-2 py-0.5 text-body-xs uppercase tracking-wide text-primary">
            {item.tag}
          </Badge>
        </div>
        <h3 className="text-body-xs sm:text-body-sm font-semibold text-foreground leading-tight">{item.title}</h3>
        <p className="text-body-xs text-muted-foreground line-clamp-2 leading-snug">{item.description}</p>
      </div>
    </motion.button>
  );
}

type RecentQuestionsProps = {
  questions: Array<{ id: string; content: string }>;
  onSelect: (content: string) => void;
};

function RecentQuestions({ questions, onSelect }: RecentQuestionsProps) {
  if (questions.length === 0) return null;
  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2 text-body-xs font-semibold uppercase tracking-wide text-muted-foreground">
        <Clock3 className="size-icon-sm" />
        Recent questions
      </div>
      <div className="flex flex-wrap gap-2">
        {questions.map((item, index) => (
          <motion.button
            key={item.id}
            type="button"
            onClick={() => onSelect(item.content)}
            className="group inline-flex items-center gap-2 rounded-full border border-border/25 bg-background/85 px-4 py-2 text-body-xs text-muted-foreground transition hover:border-primary/50 hover:text-foreground touch-manipulation"
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: index * 0.1, duration: 0.2 }}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            <MessageCircle className="size-icon-sm text-primary transition group-hover:text-primary" />
            <span className="line-clamp-1">{item.content}</span>
          </motion.button>
        ))}
      </div>
    </div>
  );
}

type ChatMessageProps = {
  message: { id: string; role: string; content: string; citations?: Array<{ url?: string | null; label?: string | null; score?: number | null }> };
  isLoading?: boolean;
  onOpenCitation?: (url: string, label?: string | null) => void;
};

function ChatMessage({ message, isLoading, onOpenCitation }: ChatMessageProps) {
  const isUser = message.role === "user";
  const thinkingPlaceholder = useMemo(() => getRandomBrainPlaceholder(), []);
  return (
    <motion.div
      layout="position"
      className={cn("flex w-full", isUser ? "justify-end" : "justify-start")}
      initial={{ opacity: 0, y: 20, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, y: -20, scale: 0.95 }}
      transition={{ duration: 0.3, ease: "easeOut" }}
    >
      <div
        className={cn(
          "max-w-[95%] sm:max-w-[85%] rounded-2xl p-4 text-body-xs sm:text-body-xs transition overflow-hidden",
          isUser
            ? "bg-primary/10 border-2 border-primary/30 text-foreground shadow-md dark:bg-primary/20 dark:border-primary/40"
            : "bg-card/80 border border-border/40 text-card-foreground shadow-lg backdrop-blur-sm dark:bg-card/60 dark:border-border/30",
        )}
      >
        <div className="mb-2 flex items-center gap-2 text-body-xs font-semibold uppercase tracking-wide">
          {isUser ? (
            <>
              <User className="size-icon-sm text-primary" />
              <span className="text-primary">You</span>
            </>
          ) : (
            <>
              <Bot className="size-icon-sm text-accent" />
              <span className="text-accent">Morty</span>
            </>
          )}
        </div>
        {message.content ? (
          isUser ? (
            <p className="min-w-0 break-words whitespace-pre-wrap text-body-xs leading-relaxed text-foreground/90 sm:text-body-xs">
              {message.content}
            </p>
          ) : (
            <>
              <MarkdownRenderer
                content={message.content}
                images={
                  Array.isArray(message.citations)
                    ? message.citations.map((item) => ({
                      url: item.url ?? null,
                      label: item.label ?? null,
                      score: item.score ?? null,
                    }))
                    : []
                }
                onImageClick={(url, label) => onOpenCitation?.(url, label)}
                className="text-foreground/90"
              />
              {isLoading && (
                <div className="mt-2 flex items-center gap-2 text-body-xs text-muted-foreground">
                  <MortyLoader size="sm" />
                  <span>Streaming response...</span>
                </div>
              )}
            </>
          )
        ) : (
          <div className="flex items-center gap-2">
            <span className="text-body-xs" aria-live="polite">
              {thinkingPlaceholder}
            </span>
            <div className="flex gap-1">
              <span className="size-2 rounded-full bg-primary/60 animate-bounce" style={{ animationDelay: "0ms" }} />
              <span className="size-2 rounded-full bg-primary/60 animate-bounce" style={{ animationDelay: "150ms" }} />
              <span className="size-2 rounded-full bg-primary/60 animate-bounce" style={{ animationDelay: "300ms" }} />
            </div>
          </div>
        )}
      </div>
    </motion.div>
  );
}

type ChatComposerProps = {
  input: string;
  onInputChange: (value: string) => void;
  isReady: boolean;
  loading: boolean;
  isSendDisabled: boolean;
  toolCallingEnabled: boolean;
  onToolToggle: (checked: boolean) => void;
  k: number;
  maxTokens: number;
  onNumberChange: (event: ChangeEvent<HTMLInputElement>, setter: (value: number) => void) => void;
  setK: (value: number) => void;
  setMaxTokens: (value: number) => void;
  isSettingsValid: boolean;
  sendMessage: (event: FormEvent<HTMLFormElement>) => void;
  error: string | null;
  reset: () => void;
  messages: Array<{ id: string; role: string; content: string }>;
};

function ChatComposer({
  input,
  onInputChange,
  isReady,
  loading,
  isSendDisabled,
  toolCallingEnabled,
  onToolToggle,
  k,
  maxTokens,
  onNumberChange,
  setK,
  setMaxTokens,
  isSettingsValid,
  sendMessage,
  error,
  reset,
  messages,
}: ChatComposerProps) {
  return (
    <motion.form
      onSubmit={sendMessage}
      className="relative z-10 px-4 pb-6 sm:px-6"
      initial={{ opacity: 0, y: 50 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: "easeOut" }}
    >
      <div className="mx-auto w-full max-w-6xl space-y-3">
        <div className="relative overflow-hidden rounded-[32px] border border-border/40 bg-background/95 p-4 shadow-xl shadow-primary/5 backdrop-blur">
          <div className="pointer-events-none absolute inset-0 rounded-[32px] border border-white/5" />
          <div className="relative z-10 flex flex-col gap-3 sm:flex-row sm:items-center sm:gap-4">
            <div className="flex-1">
              <div className="rounded-3xl border border-border/30 bg-input/10 transition focus-within:border-primary/40 focus-within:shadow-lg focus-within:shadow-primary/10">
                <Textarea
                  id="chat-input-area"
                  value={input}
                  onChange={(event) => onInputChange(event.target.value)}
                  placeholder="Ask Morty anything about your documents! He loves visual questions..."
                  disabled={!isReady}
                  rows={2}
                  className="min-h-[3.5rem] max-h-[3.5rem] w-full resize-none border-0 bg-transparent px-4 py-3 text-body leading-relaxed placeholder:text-muted-foreground outline-none focus-visible:ring-0 overflow-y-auto text-body-xs sm:text-body-xs"
                />
              </div>
            </div>
            <div className="flex w-full flex-col items-stretch gap-2 sm:w-auto sm:flex-row sm:items-center sm:gap-3">
              <AppButton
                type="submit"
                size="icon-lg"
                variant="primary"
                elevated
                disabled={isSendDisabled}
                aria-label="Send message"
              >
                {loading ? <MortyLoader size="md" /> : <Send className="size-icon-md" />}
              </AppButton>
              <div className="inline-flex items-center overflow-hidden rounded-full border border-border/40 bg-background/80 shadow-sm divide-x divide-border/40">
                <Popover>
                  <PopoverTrigger asChild>
                    <AppButton
                      type="button"
                      variant="ghost"
                      size="icon"
                      groupPosition="start"
                      aria-label="Open retrieval settings"
                    >
                      <Settings className="size-icon-sm" />
                    </AppButton>
                  </PopoverTrigger>
                  <PopoverContent className="w-80 space-y-4">
                    <div>
                      <h4 className="text-body-sm font-semibold text-foreground">Retrieval settings</h4>
                      <p className="mt-1 text-body-xs text-muted-foreground">
                        Tune how many neighbors to fetch and how long responses can be.
                      </p>
                    </div>
                    <div className="space-y-4 text-body-sm">
                      <div className="space-y-2">
                        <Label htmlFor="chat-k">Top K</Label>
                        <Input
                          id="chat-k"
                          type="number"
                          min={1}
                          value={k}
                          onChange={(event) => onNumberChange(event, setK)}
                        />
                        <p className="text-body-xs text-muted-foreground">
                          Controls how many nearest neighbors the assistant retrieves. Higher values surface more
                          context but may introduce noise.
                        </p>
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="chat-max-tokens">Max tokens</Label>
                        <Input
                          id="chat-max-tokens"
                          type="number"
                          min={64}
                          value={maxTokens}
                          onChange={(event) => onNumberChange(event, setMaxTokens)}
                        />
                        <p className="text-body-xs text-muted-foreground">
                          Control response length to balance speed with detail.
                        </p>
                      </div>
                      <div className="flex items-center justify-between gap-3 rounded-xl border border-border/30 bg-card/40 px-3 py-2">
                        <div>
                          <p className="text-body-sm font-medium text-foreground">Allow tool calling</p>
                          <p className="text-body-xs text-muted-foreground">
                            Let the assistant call retrieval tools when needed.
                          </p>
                        </div>
                        <Switch
                          id="chat-tool-calling"
                          checked={toolCallingEnabled}
                          onCheckedChange={onToolToggle}
                        />
                      </div>
                      {!isSettingsValid && (
                        <div className="flex items-center gap-2 rounded-lg border border-destructive/40 bg-destructive/10 px-3 py-2 text-body-xs text-destructive">
                          <AlertCircle className="size-icon-sm" />
                          The selected Top K value is not valid.
                        </div>
                      )}
                    </div>
                  </PopoverContent>
                </Popover>
                <AppButton
                  type="button"
                  onClick={reset}
                  variant="ghost"
                  size="icon"
                  groupPosition="end"
                  disabled={messages.length === 0 && !input}
                  aria-label="Clear conversation"
                >
                  <Trash2 className="size-icon-sm" />
                </AppButton>
              </div>
            </div>
          </div>
        </div>
        {error && (
          <div className="flex items-center gap-2 rounded-lg border border-destructive/40 bg-destructive/10 px-3 py-2 text-body-sm font-medium text-destructive">
            <AlertCircle className="size-icon-sm" />
            {error}
          </div>
        )}
      </div>
    </motion.form>
  );
}

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
    maxTokens,
    setMaxTokens,
    imageGroups,
    isSettingsValid,
    sendMessage,
    reset,
  } = useChat();
  const { isReady } = useSystemStatus();

  const [lightboxOpen, setLightboxOpen] = useState(false);
  const [lightboxSrc, setLightboxSrc] = useState<string>("");
  const [lightboxAlt, setLightboxAlt] = useState<string | null>(null);

  const endOfMessagesRef = useRef<HTMLDivElement | null>(null);
  const scrollAreaRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    // Only auto-scroll when a new message is added, not during loading
    if (messages.length > 0 && !loading) {
      const timer = setTimeout(() => {
        endOfMessagesRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
      }, 100);
      return () => clearTimeout(timer);
    }
  }, [messages.length]);

  const recentQuestions = useMemo(
    () =>
      messages
        .filter((msg) => msg.role === "user" && msg.content.trim().length > 0)
        .slice(-6)
        .reverse(),
    [messages],
  );

  const isSendDisabled = loading || !isReady || !input.trim() || !isSettingsValid;

  const handleNumberChange = (event: ChangeEvent<HTMLInputElement>, setter: (value: number) => void) => {
    const next = Number.parseInt(event.target.value, 10);
    if (!Number.isNaN(next)) {
      setter(next);
    }
  };

  const handleSuggestionClick = (prompt: string) => {
    setInput(prompt);
    const area = document.getElementById("chat-input-area");
    if (area instanceof HTMLTextAreaElement) {
      area.focus();
    }
  };

  const heroMeta = (
    <>
      <MortyMetaCard
        label="Morty's real-time chat arcade"
        title="Gamer Morty loves fast back-and-forth conversations while he anchors answers to your documents."
        bullets={[
          {
            icon: Bot,
            text: "Streams grounded responses and visual citations as Morty reasons.",
          },
          {
            icon: MessageCircle,
            text: "Keeps multi-turn context so follow-up questions stay natural.",
          },
          {
            icon: Wand2,
            text: "Switch tool calling on demand when you need deeper dives.",
          },
        ]}
        image={{
          src: "/vultr/morty/gamer_morty_nobg.png",
          alt: "Gamer Morty ready for chat",
          width: 300,
          height: 300,
        }}
      />
      <HeroMetaGroup>
        {isReady && (
          <HeroMetaPill icon={Sparkles} tone="success">
            Connected to workspace
          </HeroMetaPill>
        )}
        {timeToFirstTokenMs !== null ? (
          <HeroMetaPill icon={Timer} tone="info">
            {(timeToFirstTokenMs / 1000).toFixed(2)}s response time
          </HeroMetaPill>
        ) : null}
        {toolCallingEnabled ? (
          <HeroMetaPill icon={Bot}>
            Tool calling enabled
          </HeroMetaPill>
        ) : null}
      </HeroMetaGroup>
    </>
  );

  const handleCitationOpen = (url: string, label?: string | null) => {
    if (!url) {
      return;
    }
    setLightboxSrc(url);
    setLightboxAlt(label ?? null);
    setLightboxOpen(true);
  };

  return (
    <>
      <RoutePageShell
        eyebrow="Services"
        title="Chat with Morty, Your Visual Retrieval Buddy"
        description="Have a conversation with Morty about your documents. He understands images, charts, and text to give you grounded, visual answers."
        meta={heroMeta}
        innerClassName="flex min-h-0 flex-1 flex-col"
        variant="compact"
      >
        <motion.section
          className="relative flex flex-1 flex-col overflow-hidden"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, ease: "easeOut" }}
        >
          <div className="relative flex flex-1 overflow-hidden">
            <ScrollArea className="h-[60vh] w-full max-w-6xl mx-auto">
              <div className="space-y-6 px-6 pb-6 pr-4 sm:px-10 min-h-full">
                <AnimatePresence initial={false}>
                  {messages.length === 0 && (
                    <motion.div
                      layout
                      className="flex justify-center"
                      initial={{ opacity: 0, y: 24 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -24 }}
                      transition={{ duration: 0.3, ease: "easeInOut" }}
                    >
                      <div className="w-full max-w-3xl space-y-3 rounded-xl border border-border/20 bg-card/60 p-4 shadow-sm animate-in fade-in duration-500 dark:bg-card/40">
                        <div className="space-y-2.5">
                          <div className="flex items-center justify-center gap-2 text-body-xs font-semibold uppercase tracking-wide text-muted-foreground">
                            <Sparkles className="size-icon-sm text-primary" />
                            Try asking
                          </div>
                          <div className="grid gap-2 sm:grid-cols-2">
                            {starterPrompts.map((item, index) => (
                              <motion.div
                                key={item.prompt}
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: 0.1 + index * 0.1, duration: 0.3 }}
                              >
                                <StarterPromptItem item={item} onClick={handleSuggestionClick} />
                              </motion.div>
                            ))}
                          </div>
                        </div>
                        <RecentQuestions questions={recentQuestions} onSelect={handleSuggestionClick} />
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>

                <AnimatePresence mode="popLayout">
                  {messages.map((message, index) => {
                    const isLastMessage = index === messages.length - 1;
                    const isLastAssistantMessage = isLastMessage && message.role === "assistant";
                    return (
                      <ChatMessage
                        key={message.id}
                        message={message}
                        isLoading={loading && isLastAssistantMessage}
                        onOpenCitation={handleCitationOpen}
                      />
                    );
                  })}
                </AnimatePresence>

                <AnimatePresence mode="wait">
                  {loading && messages.length === 0 && (
                    <ChatMessage
                      key="loading"
                      message={{ id: "loading", role: "assistant", content: "" }}
                      isLoading={true}
                    />
                  )}
                </AnimatePresence>
                <div ref={endOfMessagesRef} />
              </div>
            </ScrollArea>
          </div>
        </motion.section>
        <ChatComposer
          input={input}
          onInputChange={setInput}
          isReady={isReady}
          loading={loading}
          isSendDisabled={isSendDisabled}
          toolCallingEnabled={toolCallingEnabled}
          onToolToggle={setToolCallingEnabled}
          k={k}
          maxTokens={maxTokens}
          onNumberChange={handleNumberChange}
          setK={setK}
          setMaxTokens={setMaxTokens}
          isSettingsValid={isSettingsValid}
          sendMessage={sendMessage}
          error={error}
          reset={reset}
          messages={messages}
        />
      </RoutePageShell>
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
    </>
  );
}
