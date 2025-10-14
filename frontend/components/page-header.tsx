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
      <div className="flex flex-wrap items-start gap-3">
        {Icon && (
          <div className="flex size-10 items-center justify-center rounded-md bg-primary/10 text-primary">
            <Icon className="h-5 w-5" />
          </div>
        )}
        <div className="flex flex-1 flex-col gap-2">
          <h1 className="text-2xl font-semibold text-foreground sm:text-3xl">{title}</h1>
          {description && <p className="text-sm text-muted-foreground sm:text-base">{description}</p>}
          {children}
        </div>
        {badge}
      </div>
    </div>
  );
}
