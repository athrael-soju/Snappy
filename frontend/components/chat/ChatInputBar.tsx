"use client";

import React from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { MessageSquare, Send, Loader2, Trash2 } from "lucide-react";
import ChatSettings from "@/components/chat-settings";

export interface ChatInputBarProps {
  input: string;
  setInput: (v: string) => void;
  placeholder: string;
  loading: boolean;
  isSettingsValid: boolean;
  uiSettingsValid: boolean;
  setUiSettingsValid: (v: boolean) => void;
  onSubmit: (e: React.FormEvent) => void;
  k: number;
  setK: (k: number) => void;
  toolCallingEnabled: boolean;
  setToolCallingEnabled: (v: boolean) => void;
  topK: number;
  setTopK: (v: number) => void;
  maxTokens: number;
  setMaxTokens: (v: number) => void;
  onClear: () => void;
  hasMessages?: boolean;
}

export default function ChatInputBar({
  input,
  setInput,
  placeholder,
  loading,
  isSettingsValid,
  uiSettingsValid,
  setUiSettingsValid,
  onSubmit,
  k,
  setK,
  toolCallingEnabled,
  setToolCallingEnabled,
  topK,
  setTopK,
  maxTokens,
  setMaxTokens,
  onClear,
  hasMessages = false,
}: ChatInputBarProps) {
  const disableSend = loading || !input.trim() || !isSettingsValid || !uiSettingsValid;

  return (
    <form onSubmit={onSubmit} className="flex flex-col gap-3" aria-label="Chat composer">
      <div className="flex items-end gap-3">
        <div className="relative flex-1">
          <MessageSquare className="pointer-events-none absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder={placeholder}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={loading}
            aria-label="Chat input"
            className="h-14 rounded-2xl border border-muted bg-[color:var(--surface-0)]/95 pl-12 pr-24 text-base shadow-[var(--shadow-1)] transition focus-visible:border-ring focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-[color:var(--surface-0)] disabled:opacity-70"
          />
          <div className="pointer-events-none absolute right-4 top-1/2 hidden -translate-y-1/2 items-center gap-1 rounded-full bg-[color:var(--surface-2)]/80 px-3 py-1 text-xs font-medium text-muted-foreground sm:flex">
            <kbd className="rounded-md bg-[color:var(--surface-0)] px-1.5 py-0.5 text-[10px] font-semibold text-foreground/80 shadow-sm">Shift</kbd>
            +
            <kbd className="rounded-md bg-[color:var(--surface-0)] px-1.5 py-0.5 text-[10px] font-semibold text-foreground/80 shadow-sm">Enter</kbd>
            <span>newline</span>
          </div>
        </div>

        <Tooltip>
          <TooltipTrigger asChild>
            <div>
              <ChatSettings
                k={k}
                setK={setK}
                loading={loading}
                onValidityChange={setUiSettingsValid}
                toolCallingEnabled={toolCallingEnabled}
                setToolCallingEnabled={setToolCallingEnabled}
                topK={topK}
                setTopK={setTopK}
                maxTokens={maxTokens}
                setMaxTokens={setMaxTokens}
                className="h-12 w-12"
              />
            </div>
          </TooltipTrigger>
          <TooltipContent sideOffset={8}>Chat settings</TooltipContent>
        </Tooltip>

        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              type="button"
              onClick={onClear}
              disabled={loading || !hasMessages}
              size="icon"
              variant="ghost"
              className="h-12 w-12 rounded-xl border border-muted bg-[color:var(--surface-1)]/80 text-muted-foreground transition hover:border-destructive/40 hover:bg-destructive/10 hover:text-destructive focus-visible:ring-2 focus-visible:ring-ring/40"
            >
              <Trash2 className="h-5 w-5" />
            </Button>
          </TooltipTrigger>
          <TooltipContent sideOffset={8}>
            <p>{hasMessages ? "Clear conversation" : "No messages to clear"}</p>
          </TooltipContent>
        </Tooltip>

        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              type="submit"
              disabled={disableSend}
              className="primary-gradient h-14 rounded-2xl px-6 text-base font-semibold shadow-[var(--shadow-2)] transition hover:-translate-y-0.5 focus-visible:ring-2 focus-visible:ring-ring/40 focus-visible:ring-offset-2 focus-visible:ring-offset-[color:var(--surface-0)] disabled:opacity-70"
            >
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                  Sending
                </>
              ) : (
                <>
                  <Send className="mr-2 h-5 w-5" />
                  Send
                </>
              )}
            </Button>
          </TooltipTrigger>
          <TooltipContent sideOffset={8}>
            <p>{disableSend ? "Enter a message to send" : "Send message"}</p>
          </TooltipContent>
        </Tooltip>
      </div>
    </form>
  );
}

