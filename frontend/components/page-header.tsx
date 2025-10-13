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
    <div className="w-full rounded-3xl border border-border/60 bg-card/80 px-6 py-6 shadow-sm">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center">
          {Icon && (
            <span className="flex h-12 w-12 items-center justify-center rounded-2xl bg-primary/10 text-primary">
              <Icon className="h-6 w-6" />
            </span>
          )}
          <div className="flex flex-col gap-2 text-center sm:text-left">
            <div className="flex flex-col items-center gap-2 sm:flex-row sm:items-center sm:gap-3">
              <h1 className="text-balance text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
                {title}
              </h1>
              {tooltip && (
                <Tooltip>
                  <TooltipTrigger asChild>
                    <button
                      type="button"
                      className="inline-flex h-8 w-8 items-center justify-center rounded-full border border-border/70 bg-card/90 text-muted-foreground transition-colors hover:border-primary/40 hover:text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40"
                    >
                      <HelpCircle className="h-4 w-4" />
                    </button>
                  </TooltipTrigger>
                  <TooltipContent className="max-w-xs text-sm leading-relaxed">
                    {tooltip}
                  </TooltipContent>
                </Tooltip>
              )}
            </div>
            {description && (
              <p className="text-base leading-relaxed text-muted-foreground">
                {description}
              </p>
            )}
          </div>
        </div>
        {badge && <div className="flex items-center justify-center">{badge}</div>}
      </div>
      {children && <div className="mt-4">{children}</div>}
    </div>
  );
}
