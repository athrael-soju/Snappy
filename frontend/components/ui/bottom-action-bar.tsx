import { cn } from "@/lib/utils";
import { ReactNode } from "react";
import { Badge } from "@/components/ui/badge";

interface BottomActionBarProps {
  children: ReactNode;
  className?: string;
  environment?: "Local" | "Dev" | "Prod";
}

export function BottomActionBar({
  children,
  className,
  environment,
}: BottomActionBarProps) {
  return (
    <div
      className={cn(
        "sticky bottom-0 left-0 right-0 border-t border-border/50 bg-card/95 backdrop-blur-md px-4 py-4",
        className
      )}
    >
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-3 flex-1">{children}</div>
        {environment && (
          <Badge
            variant={
              environment === "Prod"
                ? "destructive"
                : environment === "Dev"
                ? "default"
                : "secondary"
            }
            className="text-xs font-medium"
          >
            {environment}
          </Badge>
        )}
      </div>
    </div>
  );
}
