import { LucideIcon, HelpCircle } from "lucide-react";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";

import type { ReactNode } from "react";

interface PageHeaderProps {
  title: string;
  description?: string;
  icon?: LucideIcon;
  children?: ReactNode;
  badge?: ReactNode;
  tooltip?: string;
}

export function PageHeader({ title, description, icon: Icon, children, badge, tooltip }: PageHeaderProps) {
  return (
    <div className="relative space-y-3 text-center">
      {/* Subtle background accent - only on top */}
      <div className="pointer-events-none absolute inset-0 -z-10">
        <div
          className="absolute left-1/2 top-[-18%] h-56 w-56 -translate-x-1/2 rounded-full opacity-20 blur-3xl"
          style={{ background: "radial-gradient(circle, rgba(251, 226, 167, 0.35) 0%, transparent 70%)" }}
        />
      </div>

      <div className="relative z-10 flex flex-wrap items-center justify-center gap-3">
        {Icon && (
          <div className="rounded-2xl border border-border bg-card p-2.5 shadow-sm">
            <Icon className="h-6 w-6 text-primary" />
          </div>
        )}
        <div className="flex flex-wrap items-center justify-center gap-3">
          <div className="flex items-center gap-2 px-6 py-3 rounded-2xl bg-card/90 backdrop-blur-sm border border-border shadow-sm">
            <h1
              className="text-balance text-4xl font-semibold tracking-tight bg-clip-text text-transparent"
              style={{ backgroundImage: "var(--nav-pill-active)" }}
            >
              {title}
            </h1>
            {tooltip && (
              <Tooltip>
                <TooltipTrigger asChild>
                  <button
                    type="button"
                    className="inline-flex items-center justify-center rounded-full border border-border bg-card/80 p-1.5 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/40"
                  >
                    <HelpCircle className="h-4 w-4" />
                  </button>
                </TooltipTrigger>
                <TooltipContent sideOffset={8}>
                  {tooltip}
                </TooltipContent>
              </Tooltip>
            )}
          </div>
          {badge && <div className="flex items-center text-sm">{badge}</div>}
        </div>
      </div>
      {description && (
        <p className="relative z-10 mx-auto max-w-2xl text-balance text-base text-muted-foreground px-4 py-2 rounded-lg bg-card/50 backdrop-blur-sm">
          {description}
        </p>
      )}
      {children}
    </div>
  );
}
