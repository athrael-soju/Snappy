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
      <div className="flex items-center gap-2 sm:gap-3">
        <div className="relative flex-1">
          <Input
            placeholder={placeholder}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={loading}
            aria-label="Chat input"
            className="h-12 sm:h-14 rounded-2xl pl-10 sm:pl-12 pr-3 sm:pr-4 text-sm sm:text-base bg-background/50 backdrop-blur-sm transition-all focus:bg-background/80"
          />
          <MessageSquare className="pointer-events-none absolute left-3 sm:left-4 top-1/2 h-4 w-4 sm:h-5 sm:w-5 -translate-y-1/2 text-muted-foreground" />
        </div>

        {/* Button Group: Settings + Clear */}
        <div className="flex items-center rounded-xl overflow-hidden border bg-card/50 backdrop-blur-sm">
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
                  className="h-10 sm:h-12 w-10 sm:w-12 rounded-none border-0 hover:bg-muted/50"
                />
              </div>
            </TooltipTrigger>
            <TooltipContent>
              Chat settings
            </TooltipContent>
          </Tooltip>

          <div className="w-px h-6 bg-border" />

          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                type="button"
                onClick={onClear}
                disabled={loading || !hasMessages}
                size="icon"
                variant="ghost"
                className="h-10 sm:h-12 w-10 sm:w-12 rounded-none hover:bg-muted/50"
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            </TooltipTrigger>
            <TooltipContent>
              {hasMessages ? "Clear conversation" : "No messages to clear"}
            </TooltipContent>
          </Tooltip>
        </div>

        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              type="submit"
              disabled={disableSend}
              size="lg"
              className="h-10 sm:h-12 rounded-xl px-4 sm:px-6 text-sm sm:text-base font-semibold"
            >
              {loading ? (
                <>
                  <Loader2 className="mr-1.5 sm:mr-2 h-4 w-4 animate-spin" />
                  <span className="hidden sm:inline">Sending</span>
                  <span className="sm:hidden">Send</span>
                </>
              ) : (
                <>
                  <Send className="mr-1.5 sm:mr-2 h-4 w-4" />
                  Send
                </>
              )}
            </Button>
          </TooltipTrigger>
          <TooltipContent>
            {disableSend ? "Enter a message" : "Send message"}
          </TooltipContent>
        </Tooltip>
      </div>
    </form>
  );
}

