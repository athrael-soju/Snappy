import { LucideIcon, HelpCircle } from "lucide-react";
import { Tooltip, TooltipContent, TooltipTrigger, TooltipProvider } from "@/components/ui/tooltip";

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
    <TooltipProvider>
      <div className="space-y-4 text-center">
        <div className="flex items-center justify-center gap-3 flex-wrap">
          {Icon && (
            <div className="flex items-center justify-center rounded-lg bg-primary/10 p-2">
              <Icon className="h-5 w-5 text-primary" />
            </div>
          )}
          
          <div className="flex items-center gap-2">
            <h1 className="text-2xl sm:text-3xl font-semibold tracking-tight">
              {title}
            </h1>
            
            {tooltip && (
              <Tooltip>
                <TooltipTrigger asChild>
                  <button
                    type="button"
                    className="inline-flex items-center justify-center rounded-full p-1 text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
                    aria-label="More information"
                  >
                    <HelpCircle className="h-4 w-4" />
                  </button>
                </TooltipTrigger>
                <TooltipContent className="max-w-sm">
                  {tooltip}
                </TooltipContent>
              </Tooltip>
            )}
          </div>

          {badge && <div>{badge}</div>}
        </div>

        {description && (
          <p className="text-sm text-muted-foreground max-w-2xl mx-auto">
            {description}
          </p>
        )}
        
        {children}
      </div>
    </TooltipProvider>
  );
}
