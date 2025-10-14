import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { CheckCircle2, AlertTriangle, RefreshCw, Loader2 } from "lucide-react";

interface SystemStatusBadgeProps {
  isReady: boolean;
  isLoading: boolean;
  onRefresh: () => void;
}

export function SystemStatusBadge({ isReady, isLoading, onRefresh }: SystemStatusBadgeProps) {
  return (
    <div className="flex flex-col gap-3">
      <Badge
        variant={isReady ? "default" : "secondary"}
        className="h-12 justify-center px-5 text-base font-semibold"
      >
        {isReady ? (
          <><CheckCircle2 className="w-5 h-5 mr-2" /> Ready</>
        ) : (
          <><AlertTriangle className="w-5 h-5 mr-2" /> Not Ready</>
        )}
      </Badge>
      <Tooltip>
        <TooltipTrigger asChild>
          <Button
            variant="outline"
            size="sm"
            onClick={onRefresh}
            disabled={isLoading}
            className="h-11 w-full border-2 border-muted bg-card text-foreground hover:bg-primary/10 hover:border-primary hover:text-primary hover:shadow-md disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 font-medium"
          >
            {isLoading ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <RefreshCw className="w-5 h-5" />
            )}
          </Button>
        </TooltipTrigger>
        <TooltipContent sideOffset={8} className="bg-popover text-popover-foreground">
          <p>{isLoading ? "Refreshing..." : "Refresh system status"}</p>
        </TooltipContent>
      </Tooltip>
    </div>
  );
}
