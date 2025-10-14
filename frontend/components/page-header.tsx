import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";

interface PageHeaderProps {
  title: string;
  description?: string;
  icon?: LucideIcon;
  badge?: ReactNode;
  children?: ReactNode;
}

export function PageHeader({ title, description, icon: Icon, badge, children }: PageHeaderProps) {
  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="flex items-start gap-3">
          {Icon && (
            <div className="flex size-10 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary">
              <Icon className="h-5 w-5" />
            </div>
          )}
          <div className="space-y-2">
            <h1 className="text-2xl font-semibold text-foreground sm:text-3xl">{title}</h1>
            {description && <p className="text-sm text-muted-foreground sm:text-base">{description}</p>}
            {children && <div className="flex flex-wrap items-center gap-2">{children}</div>}
          </div>
        </div>
        {badge && <div className="flex flex-wrap items-center gap-2 sm:self-start">{badge}</div>}
      </div>
    </div>
  );
}
