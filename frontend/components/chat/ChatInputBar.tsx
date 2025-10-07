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
          <MessageSquare className="pointer-events-none absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-muted-foreground z-10" />
          <Input
            placeholder={placeholder}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={loading}
            aria-label="Chat input"
            className="h-11 rounded-2xl border-2 border-border bg-background/95 backdrop-blur-md pl-12 pr-4 text-base shadow-sm transition-all focus-visible:border-primary/50 focus-visible:bg-background focus-visible:ring-4 focus-visible:ring-primary/10 disabled:opacity-50 disabled:cursor-not-allowed"
          />
        </div>

        {/* Button Group: Settings + Clear */}
        <div className="flex items-center rounded-xl border-2 border-border bg-background/95 backdrop-blur-md overflow-hidden">
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
                  className="h-9 w-9 rounded-none border-0 hover:bg-muted/50 transition-colors"
                />
              </div>
            </TooltipTrigger>
            <TooltipContent sideOffset={8} className="bg-popover text-popover-foreground border-border">
              Chat settings
            </TooltipContent>
          </Tooltip>

          <div className="w-px h-5 bg-border" />

          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                type="button"
                onClick={onClear}
                disabled={loading || !hasMessages}
                size="icon"
                variant="ghost"
                className="h-9 w-9 rounded-none border-0 hover:bg-muted/50 transition-colors"
                >
                <Trash2 className="h-4 w-4" />
              </Button>
            </TooltipTrigger>
            <TooltipContent sideOffset={8} className="bg-popover text-popover-foreground border-border">
              {hasMessages ? "Clear conversation" : "No messages to clear"}
            </TooltipContent>
          </Tooltip>
        </div>

        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              type="submit"
              disabled={disableSend}
              className="primary-gradient h-11 rounded-2xl px-5 text-base font-semibold shadow-lg transition-all hover:shadow-xl hover:scale-[1.02] focus-visible:ring-4 focus-visible:ring-primary/30 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100"
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
          <TooltipContent sideOffset={8} className="bg-popover text-popover-foreground border-border">
            {disableSend ? "Enter a message to send" : "Send message"}
          </TooltipContent>
        </Tooltip>
      </div>
    </form>
  );
}

