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

export interface ChatSettingsProps {
  k: number;
  setK: (k: number) => void;
  loading?: boolean;
  className?: string;
  onValidityChange?: (valid: boolean) => void;
}

export function ChatSettings({ k, setK, loading, className, onValidityChange }: ChatSettingsProps) {
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
            </div>

            <Separator className="my-2" />

            <div className="space-y-3">
              <div>
                <Label htmlFor="k-slider" className="text-sm font-medium">Sources</Label>
                <div className="mt-4">
                  <input
                    id="k-slider"
                    type="range"
                    min={1}
                    max={25}
                    step={1}
                    value={k}
                    disabled={!!loading}
                    onChange={(e) => {
                      const next = Number(e.target.value);
                      const parsed = kSchema.safeParse(next);
                      if (parsed.success) {
                        setK(parsed.data);
                        onValidityChange?.(true);
                      }
                    }}
                    className="w-full"
                    aria-valuemin={1}
                    aria-valuemax={25}
                    aria-valuenow={k}
                    aria-label="Number of sources"
                  />
                  <div className="mt-2 flex items-center justify-between text-xs text-muted-foreground">
                    <span>1 (Fast)</span>
                    <span>
                      Selected: <Badge variant="secondary" className="align-middle">{k}</Badge>
                    </span>
                    <span>25 (Broader)</span>
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
