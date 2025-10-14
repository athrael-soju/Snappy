import Link from "next/link";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { AlertTriangle, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface SystemStatusWarningProps {
  isReady: boolean;
  isLoading?: boolean;
  className?: string;
}

export function SystemStatusWarning({ isReady, isLoading = false, className }: SystemStatusWarningProps) {
  if (isReady && !isLoading) return null;

  return (
    <Alert className={cn("border border-amber-200 bg-amber-50", className)}>
      <AlertTriangle className="h-5 w-5 text-amber-600" />
      <AlertTitle className="flex items-center gap-2 text-sm font-semibold text-amber-900">
        {isLoading ? (
          <>
            <Loader2 className="h-4 w-4 animate-spin" />
            Checking services...
          </>
        ) : (
          <>
            Snappy needs a quick setup
          </>
        )}
      </AlertTitle>
      {!isLoading && (
        <AlertDescription className="text-sm text-amber-800">
          Initialize the collection and storage bucket before you upload or search.
          <Link
            href="/maintenance?section=data"
            className="ml-2 inline-flex items-center gap-1 font-medium text-amber-900 underline"
          >
            Open maintenance
          </Link>
        </AlertDescription>
      )}
    </Alert>
  );
}
