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
  onClear: () => void;
  hasMessages?: boolean; // Whether there are actual messages to clear
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
  onClear,
  hasMessages = false,
}: ChatInputBarProps) {
  return (
    <form onSubmit={onSubmit} className="flex gap-3 items-center">
      <div className="flex-1 relative">
        <MessageSquare className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-muted-foreground" />
        <Input
          placeholder={placeholder}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={loading}
          className={`flex-1 text-base pl-11 h-12 border-2 transition-all ${
            input.trim()
              ? 'border-purple-400 bg-white shadow-md focus:border-purple-500'
              : 'border-muted-foreground/20 focus:border-purple-400'
          }`}
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
            />
          </div>
        </TooltipTrigger>
        <TooltipContent>Filter responses & source count</TooltipContent>
      </Tooltip>
      
      <Tooltip>
        <TooltipTrigger asChild>
          <Button 
            type="submit" 
            disabled={loading || !input.trim() || !isSettingsValid || !uiSettingsValid}
            size="icon"
            className="w-12 h-12 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 shadow-lg rounded-xl"
          >
            {loading ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <Send className="w-5 h-5" />
            )}
          </Button>
        </TooltipTrigger>
        <TooltipContent>
          <p>{loading ? 'Sending message...' : 'Send message'}</p>
        </TooltipContent>
      </Tooltip>
      
      <Tooltip>
        <TooltipTrigger asChild>
          <Button
            type="button"
            onClick={onClear}
            disabled={loading || !hasMessages}
            size="icon"
            variant="outline"
            className="w-12 h-12 rounded-xl border-2 border-purple-200 hover:border-purple-400 hover:bg-gradient-to-r hover:from-purple-50 hover:to-pink-50 text-muted-foreground hover:text-purple-600 transition-all duration-300 shadow-sm hover:shadow-md disabled:opacity-50"
          >
            <Trash2 className="w-5 h-5" />
          </Button>
        </TooltipTrigger>
        <TooltipContent>
          <p>{hasMessages ? 'Clear conversation' : 'No conversation to clear'}</p>
        </TooltipContent>
      </Tooltip>
    </form>
  );
}
