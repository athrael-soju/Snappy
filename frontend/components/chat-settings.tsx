"use client";

import React from "react";
import { Button } from "@/components/ui/button";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogTrigger, DialogClose } from "@/components/ui/dialog";
import { Separator } from "@/components/ui/separator";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectGroup, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { SlidersHorizontal } from "lucide-react";
import { kSchema } from "@/lib/validation/chat";

export type KMode = "auto" | "manual";

export interface ChatSettingsProps {
  k: number;
  kMode: KMode;
  setK: (k: number) => void;
  setKMode: (mode: KMode) => void;
  loading?: boolean;
  className?: string;
  onValidityChange?: (valid: boolean) => void;
  toolsEnabled?: boolean;
  setToolsEnabled?: (v: boolean) => void;
  model?: 'gpt-5' | 'gpt-5-mini' | 'gpt-5-nano';
  setModel?: (m: 'gpt-5' | 'gpt-5-mini' | 'gpt-5-nano') => void;
}

// Slider-based UI replaces presets

export function ChatSettings({ k, kMode, setK, setKMode, loading, className, onValidityChange, toolsEnabled = true, setToolsEnabled, model = 'gpt-5-mini', setModel }: ChatSettingsProps) {
  const selectedKey = kMode === "auto" ? "auto" : String(k);
  const [customError, setCustomError] = React.useState<string>("");
  const [open, setOpen] = React.useState(false);

  const isCurrentValid = React.useMemo(() => {
    if (kMode === "auto") return true;
    return kSchema.safeParse(k).success && !customError;
  }, [kMode, k, customError, kSchema]);

  const handleAutoToggle = (enabled: boolean) => {
    if (enabled) {
      setKMode("auto");
      setCustomError("");
      onValidityChange?.(true);
    } else {
      setKMode("manual");
      const parsed = kSchema.safeParse(k);
      if (!parsed.success) {
        setCustomError(parsed.error.issues[0]?.message ?? "Invalid value");
        onValidityChange?.(false);
      } else {
        setCustomError("");
        onValidityChange?.(true);
      }
    }
  };

  const handleSlider = (val: number) => {
    setKMode("manual");
    const parsed = kSchema.safeParse(val);
    if (parsed.success) {
      setK(parsed.data);
      setCustomError("");
      onValidityChange?.(true);
    } else {
      setCustomError(parsed.error.issues[0]?.message ?? "Invalid value");
      onValidityChange?.(false);
    }
  };

  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <Dialog
          open={open}
          onOpenChange={(v) => {
            if (!v && !isCurrentValid) {
              // Block closing when invalid
              return;
            }
            setOpen(v);
          }}
        >
          <DialogTrigger asChild>
            <Button type="button" variant="outline" size="icon" className={className ?? "h-12 w-12"} aria-label="Chat settings">
              <SlidersHorizontal className="w-5 h-5" />
            </Button>
          </DialogTrigger>
          <DialogContent
            aria-label="Chat settings"
            onInteractOutside={(e) => {
              if (!isCurrentValid) e.preventDefault();
            }}
            onEscapeKeyDown={(e) => {
              if (!isCurrentValid) e.preventDefault();
            }}
          >
            <div className="flex items-start justify-between gap-2">
              <DialogHeader className="space-y-1">
                <DialogTitle className="text-lg font-semibold">Chat settings</DialogTitle>
                <DialogDescription>
                  Choose how many sources are used to answer your question. Fewer sources = faster responses. More sources = broader context.
                </DialogDescription>
              </DialogHeader>
            </div>

            <Separator className="my-2" />

            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex flex-col">
                  <Label className="text-sm font-medium">Enable tools</Label>
                  <span className="text-xs text-muted-foreground">Use image_search on knowledgebase questions only</span>
                </div>
                <Switch
                  checked={!!toolsEnabled}
                  onCheckedChange={(v) => setToolsEnabled?.(Boolean(v))}
                  aria-label="Enable tools"
                />
              </div>

              <div className="flex items-center justify-between">
                <div className="flex flex-col">
                  <Label className="text-sm font-medium">OpenAI model</Label>
                  <span className="text-xs text-muted-foreground">Choose model to use</span>
                </div>
                <div className="w-30">
                  <Select
                    value={model}
                    onValueChange={(v) => setModel?.(v as 'gpt-5' | 'gpt-5-mini' | 'gpt-5-nano')}
                    disabled={!!loading}
                  >
                    <SelectTrigger aria-label="OpenAI model" className="h-8 w-full text-sm">
                      <SelectValue placeholder="Select model" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectGroup>
                        <SelectItem value="gpt-5">gpt-5</SelectItem>
                        <SelectItem value="gpt-5-mini">gpt-5-mini</SelectItem>
                        <SelectItem value="gpt-5-nano">gpt-5-nano</SelectItem>
                      </SelectGroup>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div>
                <Label className="text-sm font-medium">Sources</Label>
                <div className="mt-2 space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex flex-col">
                      <span className="text-sm">Auto</span>
                      <span className="text-xs text-muted-foreground">The AI Assistant will choose the number of sources based on your question.</span>
                    </div>
                    <Switch
                      checked={kMode === 'auto'}
                      onCheckedChange={(v) => handleAutoToggle(Boolean(v))}
                      disabled={!!loading}
                      aria-label="Auto-select sources"
                    />
                  </div>

                  <div className={`rounded-md border p-3 ${kMode === 'auto' ? 'opacity-50' : ''}`} aria-disabled={kMode === 'auto'}>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm text-muted-foreground">Number of sources</span>
                      <span className="text-sm font-medium">{k}</span>
                    </div>
                    <input
                      type="range"
                      min={1}
                      max={25}
                      step={1}
                      value={k}
                      onChange={(e) => handleSlider(parseInt(e.target.value, 10))}
                      disabled={kMode === 'auto' || !!loading}
                      aria-label="Number of sources"
                      className="w-full"
                    />
                    {customError && (
                      <p className="text-xs text-destructive mt-2" role="alert">{customError}</p>
                    )}
                  </div>
                </div>
              </div>
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
