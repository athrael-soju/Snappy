"use client";

import React from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { MessageSquare, Send, Loader2 } from "lucide-react";
import SourcesControl from "@/components/sources-control";
import type { KMode } from "@/components/sources-control";

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
  kMode: KMode;
  setK: (k: number) => void;
  setKMode: (m: KMode) => void;
  toolsEnabled: boolean;
  setToolsEnabled: (v: boolean) => void;
  model: 'gpt-5' | 'gpt-5-mini' | 'gpt-5-nano';
  setModel: (m: 'gpt-5' | 'gpt-5-mini' | 'gpt-5-nano') => void;
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
  kMode,
  setK,
  setKMode,
  toolsEnabled,
  setToolsEnabled,
  model,
  setModel,
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
            <SourcesControl 
              k={k}
              kMode={kMode}
              setK={setK}
              setKMode={setKMode}
              loading={loading}
              onValidityChange={setUiSettingsValid}
              toolsEnabled={toolsEnabled}
              setToolsEnabled={setToolsEnabled}
              model={model}
              setModel={setModel}
            />
          </div>
        </TooltipTrigger>
        <TooltipContent>Filter responses & source count</TooltipContent>
      </Tooltip>
      <Button 
        type="submit" 
        disabled={loading || !input.trim() || !isSettingsValid || !uiSettingsValid}
        size="lg"
        className="px-6 h-12 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 shadow-lg"
      >
        {loading ? (
          <>
            <Loader2 className="w-5 h-5 animate-spin" />
          </>
        ) : (
          <>
            <Send className="w-5 h-5" />
          </>
        )}
      </Button>
    </form>
  );
}
