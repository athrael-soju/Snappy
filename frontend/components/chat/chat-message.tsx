"use client";

import { useMemo } from "react";
import { motion } from "framer-motion";
import { Loader2, Bot, User } from "lucide-react";
import MarkdownRenderer from "@/components/chat/MarkdownRenderer";
import { getRandomBrainPlaceholder } from "@/lib/chat/brain-states";
import { cn } from "@/lib/utils";

export type ChatCitation = { url?: string | null; label?: string | null; score?: number | null };

export type ChatMessageBubbleProps = {
    message: { id: string; role: string; content: string; citations?: ChatCitation[] };
    isLoading?: boolean;
    onOpenCitation?: (url: string, label?: string | null) => void;
};

export function ChatMessageBubble({ message, isLoading, onOpenCitation }: ChatMessageBubbleProps) {
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
                    "max-w-[95%] sm:max-w-[85%] rounded-2xl p-4 text-body-sm sm:text-body transition overflow-hidden",
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
                            <span className="text-accent">Assistant</span>
                        </>
                    )}
                </div>
                {message.content ? (
                    isUser ? (
                        <p className="min-w-0 break-words whitespace-pre-wrap text-body-sm leading-relaxed text-foreground/90 sm:text-body">
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
                                    <Loader2 className="size-icon-sm animate-spin" />
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
