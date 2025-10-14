"use client";

import React from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogTrigger } from "@/components/ui/dialog";
import { Separator } from "@/components/ui/separator";
import { Label } from "@/components/ui/label";
import { SlidersHorizontal } from "lucide-react";
import { kSchema } from "@/lib/validation/chat";
import { Switch } from "@/components/ui/switch";

export interface ChatSettingsProps {
  k: number;
  setK: (k: number) => void;
  loading?: boolean;
  className?: string;
  onValidityChange?: (valid: boolean) => void;
  toolCallingEnabled?: boolean;
  setToolCallingEnabled?: (v: boolean) => void;
  topK?: number;
  setTopK?: (v: number) => void;
  maxTokens?: number;
  setMaxTokens?: (v: number) => void;
  showMaxTokens?: boolean; // Whether to show max tokens setting (only for chat, not search)
}

export function ChatSettings({ k, setK, loading, className, onValidityChange, toolCallingEnabled, setToolCallingEnabled, topK = 16, setTopK, maxTokens = 500, setMaxTokens, showMaxTokens = true }: ChatSettingsProps) {
  const [open, setOpen] = React.useState(false);

  // Slider always enforces bounds; always valid
  React.useEffect(() => {
    onValidityChange?.(true);
  }, [onValidityChange]);

  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger asChild>
            <Button type="button" variant="ghost" size="icon" className={className ?? "h-12 w-12"} aria-label="Chat settings">
              <SlidersHorizontal className="h-4 w-4 sm:h-5 sm:w-5" />
            </Button>
          </DialogTrigger>
          <DialogContent aria-label="Chat settings">
            <div className="flex items-start justify-between gap-2">
              <DialogHeader className="space-y-1">
                <DialogTitle className="text-lg font-semibold">{showMaxTokens ? 'Chat' : 'Search'} settings</DialogTitle>
                <DialogDescription>
                  Configure your {showMaxTokens ? 'chat' : 'search'} preferences and result settings.
                </DialogDescription>
              </DialogHeader>
            </div>

            <Separator className="my-2" />

            <div className="space-y-4">
              {showMaxTokens && toolCallingEnabled !== undefined && setToolCallingEnabled && (
                <div className="flex items-center justify-between">
                  <div className="space-y-1">
                    <Label htmlFor="tool-calling" className="text-sm font-medium">Tool calling</Label>
                    <p className="text-xs text-muted-foreground">When disabled, the assistant will always use the knowledge base (no tool calls).</p>
                  </div>
                  <Switch
                    id="tool-calling"
                    checked={toolCallingEnabled}
                    onCheckedChange={(v) => setToolCallingEnabled?.(!!v)}
                    disabled={!!loading}
                    aria-label="Enable tool calling"
                  />
                </div>
              )}

              <div>
                <Label htmlFor="topk-slider" className="text-sm font-medium">Search Results</Label>
                <p className="text-xs text-muted-foreground mb-4">Number of search results to return (1-100)</p>
                <div className="mt-4">
                  <input
                    id="topk-slider"
                    type="range"
                    min={1}
                    max={100}
                    step={1}
                    value={topK}
                    disabled={!!loading}
                    onChange={(e) => {
                      const next = Number(e.target.value);
                      if (next >= 1 && next <= 100) {
                        setTopK?.(next);
                        // Also update k to match topK
                        const parsed = kSchema.safeParse(Math.min(next, 25));
                        if (parsed.success) {
                          setK(parsed.data);
                          onValidityChange?.(true);
                        }
                      }
                    }}
                    className="w-full"
                    aria-valuemin={1}
                    aria-valuemax={100}
                    aria-valuenow={topK}
                    aria-label="Search Results"
                  />
                  <div className="mt-2 flex items-center justify-between text-xs text-muted-foreground">
                    <span>1</span>
                    <span>
                      Selected: <Badge variant="secondary" className="align-middle">{topK}</Badge>
                    </span>
                    <span>100</span>
                  </div>
                </div>
              </div>

              {showMaxTokens && (
                <div>
                  <Label htmlFor="maxtokens-slider" className="text-sm font-medium">Max Tokens</Label>
                  <p className="text-xs text-muted-foreground mb-4">Maximum tokens for text generation (100-4096)</p>
                  <div className="mt-4">
                    <input
                      id="maxtokens-slider"
                      type="range"
                      min={100}
                      max={4096}
                      step={1}
                      value={maxTokens}
                      disabled={!!loading}
                      onChange={(e) => {
                        const next = Number(e.target.value);
                        if (next >= 100 && next <= 4096) {
                          setMaxTokens?.(next);
                        }
                      }}
                      className="w-full"
                      aria-valuemin={100}
                      aria-valuemax={4096}
                      aria-valuenow={maxTokens}
                      aria-label="Max Tokens"
                    />
                    <div className="mt-2 flex items-center justify-between text-xs text-muted-foreground">
                      <span>100</span>
                      <span>
                        Selected: <Badge variant="secondary" className="align-middle">{maxTokens}</Badge>
                      </span>
                      <span>4096</span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </DialogContent>
        </Dialog>
      </TooltipTrigger>
      <TooltipContent>
        <p>Chat settings</p>
      </TooltipContent>
    </Tooltip>
  );
}

export default ChatSettings;
