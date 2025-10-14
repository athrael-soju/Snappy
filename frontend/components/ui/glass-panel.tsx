import { cn } from "@/lib/utils";
import { ReactNode } from "react";

interface GlassPanelProps {
  children: ReactNode;
  className?: string;
  hover?: boolean;
}

export function GlassPanel({ children, className, hover = false }: GlassPanelProps) {
  return (
    <div
      className={cn(
        "w-full rounded-2xl bg-card/50 backdrop-blur-xl border border-border/30 shadow-xl transition-all duration-300 ease-out",
        hover && "hover:bg-card/60 hover:shadow-2xl hover:scale-[1.01] hover:border-border/50",
        className
      )}
    >
      {children}
    </div>
  );
}
