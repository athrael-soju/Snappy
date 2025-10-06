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
    <div className="flex items-center gap-2">
      <Badge 
        variant={isReady ? "default" : "secondary"}
        className={`h-10 px-4 ${isReady ? 'bg-green-600 hover:bg-green-700' : 'bg-amber-500 hover:bg-amber-600'} text-white`}
      >
        {isReady ? (
          <><CheckCircle2 className="w-4 h-4 mr-2" /> Ready</>
        ) : (
          <><AlertTriangle className="w-4 h-4 mr-2" /> Not Initialized</>
        )}
      </Badge>
      <Tooltip>
        <TooltipTrigger asChild>
          <Button
            variant="outline"
            size="sm"
            onClick={onRefresh}
            disabled={isLoading}
            className="h-10"
          >
            {isLoading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <RefreshCw className="w-4 h-4" />
            )}
          </Button>
        </TooltipTrigger>
        <TooltipContent sideOffset={8}>
          <p>{isLoading ? "Refreshing..." : "Refresh system status"}</p>
        </TooltipContent>
      </Tooltip>
    </div>
  );
}
