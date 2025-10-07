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
      <div className="flex items-end gap-2.5">
        <div className="relative flex-1">
          <MessageSquare className="pointer-events-none absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder={placeholder}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={loading}
            aria-label="Chat input"
            className="h-12 rounded-2xl border border-muted/60 bg-[color:var(--surface-0)] pl-12 pr-4 text-[15px] shadow-sm transition focus-visible:border-purple-500/50 focus-visible:ring-2 focus-visible:ring-purple-500/20 focus-visible:ring-offset-1 focus-visible:ring-offset-[color:var(--surface-0)] disabled:opacity-70"
          />
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
                className="h-10 w-10"
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
              className="h-10 w-10 rounded-xl border border-muted/60 bg-[color:var(--surface-0)] text-muted-foreground transition hover:border-destructive/40 hover:bg-destructive/10 hover:text-destructive focus-visible:ring-2 focus-visible:ring-destructive/20 disabled:opacity-50"
            >
              <Trash2 className="h-4 w-4" />
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
              className="primary-gradient h-12 rounded-2xl px-6 text-[15px] font-semibold shadow-lg transition hover:shadow-xl hover:-translate-y-0.5 focus-visible:ring-2 focus-visible:ring-purple-500/40 focus-visible:ring-offset-2 focus-visible:ring-offset-[color:var(--surface-0)] disabled:opacity-70 disabled:hover:translate-y-0"
            >
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Sending
                </>
              ) : (
                <>
                  <Send className="mr-2 h-4 w-4" />
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

