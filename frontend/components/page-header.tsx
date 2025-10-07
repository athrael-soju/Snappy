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
      {/* Background decoration */}
      <div className="pointer-events-none absolute inset-0 -z-10">
        <div
          className="absolute left-1/2 top-[-18%] h-56 w-56 -translate-x-1/2 rounded-full opacity-60 blur-3xl"
          style={{ background: "radial-gradient(circle, rgba(251, 226, 167, 0.35) 0%, transparent 70%)" }}
        />
        <div
          className="absolute left-12 top-0 h-36 w-36 rounded-full opacity-35 blur-3xl"
          style={{ background: "radial-gradient(circle, rgba(228, 66, 177, 0.25) 0%, transparent 70%)" }}
        />
        <div
          className="absolute right-10 top-6 h-32 w-32 rounded-full opacity-30 blur-3xl"
          style={{ background: "radial-gradient(circle, rgba(154, 137, 247, 0.25) 0%, transparent 70%)" }}
        />
      </div>

      <div className="relative z-10 flex flex-wrap items-center justify-center gap-3">
        {Icon && (
          <div className="rounded-2xl border border-border/50 bg-card p-2.5 shadow-[0_16px_30px_-24px_rgba(251,226,167,0.75)]">
            <Icon className="h-6 w-6 text-primary" />
          </div>
        )}
        <div className="flex flex-wrap items-center justify-center gap-3">
          <div className="flex items-center gap-2 px-6 py-3 rounded-2xl bg-background/60 dark:bg-background/40 backdrop-blur-md border border-border/30 shadow-lg">
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
                    className="inline-flex items-center justify-center rounded-full border border-muted/60 bg-[color:var(--surface-1)]/80 p-1.5 text-muted-foreground transition-colors hover:bg-[color:var(--surface-2)] hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/40"
                  >
                    <HelpCircle className="h-4 w-4" />
                  </button>
                </TooltipTrigger>
                <TooltipContent className="max-w-xs text-sm bg-popover text-popover-foreground" sideOffset={8}>
                  {tooltip}
                </TooltipContent>
              </Tooltip>
            )}
          </div>
          {badge && <div className="flex items-center text-sm">{badge}</div>}
        </div>
      </div>
      {description && (
        <p className="relative z-10 mx-auto max-w-2xl text-balance text-sm text-foreground/85 sm:text-base px-4 py-2 rounded-lg bg-background/50 dark:bg-background/30 backdrop-blur-sm">
          {description}
        </p>
      )}
      {children}
    </div>
  );
}
