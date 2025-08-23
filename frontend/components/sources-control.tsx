"use client";

import React from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogTrigger, DialogClose } from "@/components/ui/dialog";
import { Separator } from "@/components/ui/separator";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { SlidersHorizontal, Check } from "lucide-react";

export type KMode = "auto" | "manual";

export interface SourcesControlProps {
  k: number;
  kMode: KMode;
  setK: (k: number) => void;
  setKMode: (mode: KMode) => void;
  loading?: boolean;
  className?: string;
}

const PRESETS = [
  { label: "Fast", value: 3 },
  { label: "Balanced", value: 5 },
  { label: "Thorough", value: 10 },
  { label: "Max", value: 20 },
] as const;

export function SourcesControl({ k, kMode, setK, setKMode, loading, className }: SourcesControlProps) {
  const isPreset = PRESETS.some(p => p.value === k);
  const selectedKey = kMode === "auto" ? "auto" : (isPreset ? String(k) : "custom");
  const [customVal, setCustomVal] = React.useState<string>(String(k));
  const handleChange = (val: string) => {
    if (val === "auto") {
      setKMode("auto");
      return;
    }
    if (val === "custom") {
      setKMode("manual");
      const n = Number(customVal);
      if (Number.isFinite(n) && n >= 1 && n <= 50) setK(Math.round(n));
      return;
    }
    const num = parseInt(val, 10);
    if (!Number.isNaN(num)) {
      setKMode("manual");
      setK(num);
    }
  };

  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <Dialog>
          <DialogTrigger asChild>
            <Button type="button" variant="outline" size="icon" className={className ?? "h-12 w-12"} aria-label="Chat settings">
              <SlidersHorizontal className="w-5 h-5" />
            </Button>
          </DialogTrigger>
          <DialogContent aria-label="Chat settings">
            <div className="flex items-start justify-between gap-2">
              <DialogHeader className="space-y-1">
                <DialogTitle className="text-lg font-semibold">Chat settings</DialogTitle>
                <DialogDescription>
                  Choose how many sources are used to answer your question. Fewer sources = faster responses. More sources = broader context.
                </DialogDescription>
              </DialogHeader>
              <DialogClose asChild>
                <Button variant="ghost" size="icon" className="h-9 w-9" aria-label="Close settings">
                  <span aria-hidden>×</span>
                </Button>
              </DialogClose>
            </div>

            <Separator className="my-2" />

            <div className="space-y-3">
              <div>
                <Label className="text-sm font-medium">Sources</Label>
                <div className="mt-2 grid gap-2 sm:grid-cols-2" role="radiogroup" aria-label="Sources selection">
                  {/* Auto option */}
                  <button
                    type="button"
                    role="radio"
                    aria-checked={selectedKey === "auto"}
                    disabled={!!loading}
                    onClick={() => handleChange("auto")}
                    className={`flex items-center justify-between rounded-md border p-2 pr-3 text-left transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 ${
                      selectedKey === "auto" ? "border-primary bg-primary/10 ring-2 ring-ring" : "hover:bg-muted"
                    }`}
                  >
                    <span className="flex items-center gap-2">
                      <span className="h-5 w-5 inline-flex rounded-full border flex items-center justify-center">
                        {selectedKey === "auto" && <Check className="h-3.5 w-3.5 text-primary" aria-hidden />}
                      </span>
                      <span className="flex flex-col">
                        <span>Auto</span>
                        <span className="text-xs text-muted-foreground">Chooses best based on your question</span>
                      </span>
                    </span>
                    <span className="sr-only">{selectedKey === "auto" ? "Selected" : ""}</span>
                  </button>

                  {/* Preset options */}
                  {PRESETS.map((p) => (
                    <Tooltip key={p.value}>
                      <button
                        type="button"
                        role="radio"
                        aria-checked={selectedKey === String(p.value)}
                        disabled={!!loading}
                        onClick={() => handleChange(String(p.value))}
                        className={`flex items-center justify-between rounded-md border p-2 pr-3 text-left transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 ${
                          selectedKey === String(p.value) ? "border-primary bg-primary/10 ring-2 ring-ring" : "hover:bg-muted"
                        }`}
                      >
                        <span className="flex items-center gap-2">
                          <span className="h-5 w-5 inline-flex rounded-full border flex items-center justify-center">
                            {selectedKey === String(p.value) && <Check className="h-3.5 w-3.5 text-primary" aria-hidden />}
                          </span>
                          <span className="flex flex-col">
                            <span className="flex items-center gap-1">
                              {p.label}
                              <Badge variant="outline" className="text-[10px] px-1 py-0 leading-none">{p.value}</Badge>
                            </span>
                            <span className="text-xs text-muted-foreground">
                              {p.value === 3 && "Quickest responses"}
                              {p.value === 5 && "Good balance of speed & context"}
                              {p.value === 10 && "Broader context"}
                              {p.value === 20 && "Deepest research"}
                            </span>
                          </span>
                        </span>
                        <span className="sr-only">{selectedKey === String(p.value) ? "Selected" : ""}</span>
                      </button>
                      <TooltipContent>
                        <p>Use approximately {p.value} sources for broader context.</p>
                      </TooltipContent>
                    </Tooltip>
                  ))}

                  {/* Custom option */}
                  <button
                    type="button"
                    role="radio"
                    aria-checked={selectedKey === "custom"}
                    disabled={!!loading}
                    onClick={() => handleChange("custom")}
                    className={`flex items-center justify-between rounded-md border p-2 pr-3 text-left transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 ${
                      selectedKey === "custom" ? "border-primary bg-primary/10 ring-2 ring-ring" : "hover:bg-muted"
                    }`}
                  >
                    <span className="flex items-center gap-2">
                      <span className="h-5 w-5 inline-flex rounded-full border flex items-center justify-center">
                        {selectedKey === "custom" && <Check className="h-3.5 w-3.5 text-primary" aria-hidden />}
                      </span>
                      <span className="flex flex-col">
                        <span>Custom</span>
                        <span className="text-xs text-muted-foreground">Set your own number</span>
                      </span>
                    </span>
                    <div className="flex items-center gap-2">
                      <Input
                        type="number"
                        min={1}
                        max={50}
                        value={customVal}
                        onChange={(e) => setCustomVal(e.target.value)}
                        onBlur={() => {
                          const n = Number(customVal);
                          if (Number.isFinite(n)) {
                            const clamped = Math.min(50, Math.max(1, Math.round(n)));
                            setCustomVal(String(clamped));
                            setKMode("manual");
                            setK(clamped);
                          }
                        }}
                        className="h-8 w-20"
                      />
                    </div>
                  </button>
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

export default SourcesControl;
