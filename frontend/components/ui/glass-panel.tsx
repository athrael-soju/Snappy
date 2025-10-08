import { cn } from "@/lib/utils";
import { ReactNode } from "react";

export type GlassDepth = "background" | "surface" | "overlay";

interface GlassPanelProps {
  children: ReactNode;
  className?: string;
  depth?: GlassDepth;
}

export function GlassPanel({ children, className, depth = "surface" }: GlassPanelProps) {
  return (
    <div
      data-glass-depth={depth}
      className={cn("glass-surface w-full rounded-3xl", className)}
    >
      {children}
    </div>
  );
}
