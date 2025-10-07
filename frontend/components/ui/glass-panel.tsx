import { cn } from "@/lib/utils";
import { ReactNode } from "react";

interface GlassPanelProps {
  children: ReactNode;
  className?: string;
}

export function GlassPanel({ children, className }: GlassPanelProps) {
  return (
    <div
      className={cn(
        "w-full rounded-3xl border border-border/50 bg-card/40 backdrop-blur-xl shadow-2xl",
        className
      )}
    >
      {children}
    </div>
  );
}
